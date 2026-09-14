# Current state / Текущее состояние

## Проверка готовности по запросу пользователя — 2026-09-14 14:37 UTC

Исходники beta08/code8: c98d789, отправлены в main. Clients34855992025:
Linux и Windows success; Android APK/unit/lint этап завершён, продолжается реальный
WG/AWG/TCP/Auto lifecycle на эмуляторе. linux-control34855991849 и phase034855991881
успешны. APK пока не подписан, не установлен и не опубликован.

Дополнительно приняты реальные HTTPS/DNS проверки персональных профилей:
TCP RU — 2a0a:2b41:0:3854::/RU; TCP NL —186.246.45.246/NL;
AWG3.1 RU —185.251.89.19/RU; AWG3.1 NL —186.246.45.246/NL.
AWG проверен в отдельных контейнерных сетях без изменения маршрутов компьютера.
Это не заменяет приёмку FriendsActivity на телефоне. ADB восстановлен через
обнаруженный mDNS порт192.168.129.42:38759; APK friends пока не установлен.

Далее: дождаться успешного Android CI, проверить digest и содержимое точного
артефакта, подписать универсальный APK beta08 локальным beta-v1 ключом, установить
отдельный пакет com.familyconnect.app.friends и проверить инвайт, четыре сочетания,
перезапуск/восстановление. Затем опубликовать APK и короткую инструкцию, выдать
коды отдельно. Rollback только friends-сервисов/HTTPS routes, существующий Pilot
сохраняется; shared credentials не восстанавливать. Desktop invite onboarding pending.


## Invite pilot checkpoint — 2026-09-14

Android 0.1.7-beta08/code8 prepared (not yet installed). Latest pushed source
a673e45: Clients34851270867 all three platforms success; phase034851271032 success.
New code: local Java/resources108 tests and invite backend3 tests passed.
HTTPS proof activation passed; second device with same invitation rejected403.
Both countries now issue individual TCP credentials and AWG3.1 peers; offline-signed
credential-free catalog sequence3 verified. Fixed Xray adu missing inbound port;
confirmation checks returned user UUID/email, because CLI exit0 alone is insufficient.
Public shared catalog withdrawn and common TCP credentials revoked on both hosts.
Separate friends-access API18084 behind8443 enabled; original product DB untouched.
Short tester manual: docs/testing/friends-quickstart.ru.md, download link pending.
Next: final CI, sign exact accepted friends APK, physical Android four combinations,
restart/recovery, private invitation batch and public APK/manual. Desktop invited
onboarding not ready. Rollback: stop only family-connect-friends-access/tcp/awg
services and remove friends HTTPS routes; keep original Pilot and product services.
Do not restore withdrawn common credentials. Earlier open-access notes are historical.


## Утверждённый порядок выпуска — 2026-09-14

Пользователь: сначала выполнить весь план VPN-сервиса на Linux, Windows и Android.
Мессенджер и iPhone отложены до завершения этого плана; текущий код мессенджера
сохраняем, новых задач по нему и iOS сейчас не начинаем. Все результаты, ограничения,
версии и оставшиеся проверки документируем. Этот порядок имеет приоритет над
историческими разделами ниже, где следующим шагом названы chat/Store bridge или iOS.

[Единый список условий выпуска](PLAN.md#release-gates-three-platforms).

## Актуальная раздаваемая сборка: одноразовые инвайты — 2026-09-14

Последнее решение пользователя: общий APK, одноразовый код на одно устройство;
после активации доступ бессрочный, без оплаты и аккаунта. Независимые селекторы:
Россия/Нидерланды и AWG3.1/TCP REALITY. Это заменяет предыдущее решение об открытом
доступе любому получившему APK и привязке транспорта к стране. Финальная сборка
ещё не выдана; beta07/08 в разработке нельзя объявлять готовой для раздачи.

Оба отдельных AWG3.1 сервиса установлены на authorized hosts: fcopen31,
UDP51823,10.84.0.1/16(RU),10.83.0.1/16(NL). Engine/tools из принятого experiment2:
e7f00e47d6df853ade5dcd2fe79240f01ff897d75088c768316a444c27c87e0f /
906d6795af1dd4adee7b11bf1e7fa133d4795c8a8d6e2099b34a026f810a3278.
AWG peer registration идемпотентна по отдельному публичному ключу телефона;
server-side SSH key допускает только registration forced command в Нидерландах.
Публичный registration HTTP пока не включён; нужен invite/proof gate.

Добавляется отдельное хранилище одноразовых инвайтов control/friends, без Django и
миграции существующей product DB. Нужно завершить proofs/atomic activation,
индивидуальные TCP credentials, автоматическую peer выдачу только активированным
устройствам, Android secure identity/cache и UI ввода кода. Удалить/заменить прежний
публичный catalog1 с общими TCP credentials и отозвать эти общие credentials до
закрытого пилота. Новый подписанный шаблон AWG/TCP пока не опубликован:
Python legacy parser отказал AWG3.1; native Java compile и108 tests passed.

RU TCP с SNI www.cloudflare.com пропустил HTTPS; внешний IP оказался IPv6
2a0a:2b41:0:3854::, locRU. Прежний assert ожидал IPv4, поэтому этот отказ проверки
не означает отказ туннеля. С SNI www.microsoft.com был реальный TLS reset.
NL TCP и все четыре комбинации на реальном Android ещё не приняты. На телефоне
по-прежнему beta05/revision9; friends APK не установлен. Следующие действия:
принять invite backend/security tests, закончить сборку и CI, подписать после gates,
установить и пройти 4 комбинации/повторный запуск/отказ повторного инвайта; затем
выдать APK и коды. Linux/Windows выдавать только при подтверждённой готовности.
Rollback только новых friends services; действующие Pilot/WG/AWG/TCP/API сохранять.

## Открытая сборка для знакомых — 2026-09-14

Пользователь явно выбрал открытый тест: любой получивший APK подключается, без
аккаунта/оплаты/срока окончания, с общим тестовым доступом к двум TCP-серверам.
Другие системы — если готовы. Эта отдельная friends-сборка не заменяет требования
managed Reticulum pipeline и не изменяет текущий Pilot/identity/journal.
Подготовлена Android0.1.6-beta07/code7, com.familyconnect.app.friends, non-debuggable:
выбор RU/NL, connect/disconnect, bound IP check; HTTPS signed open-test catalog,
strict profiles, monotonic cache, отсутствие lease/payment gate. Local Java/resources
compilation и108 tests passed. CI/подписание/установка/реальный телефон ещё впереди.

Два отдельных TCP services Xray26.3.27/d2758a0 enabled/active:
185.251.89.19:8446 и186.246.45.246:443; server private keys разные, credentials
предназначены для общего открытого теста. Original API/VPN не изменены. HTTPS
/friends/catalog.json опубликован; bytes match offline signed catalog sequence1,
SHA256572aac4bfe61080ec6ea931e8a18c6dcd1bfd695f0d1484535f633945fd8a13c.
Root signing key остаётся только локально. Native/HTTP traffic gates pending.

Предшествующая beta06/source01fe2bf: Clients34849209625 Android/Linux/Windows success,
phase034849209570 success; APK ещё не подписан/установлен. Приоритет переключён на
запрошенную раздаваемую friends-сборку; на Redmi пока прежний рабочий beta05/revision9.
Далее CI beta07, обе страны на реальном Android и повторная установка/перезапуск;
ссылки на готовые артефакты и ограничения desktop readiness. Desktop0.2.9 пока не имеет
этого автоматического открытого onboarding; не выдавать его за такую же готовую сборку.
[Rollout/rollback](../deploy/friends/README.md).

## Android: выбор России / Нидерландов — 2026-09-14

По запросу пользователя добавлен выбор шлюза из действующей подписанной конфигурации.
Имена pilot gateways: tcp-android-pilot — «Россия» (185.251.89.19, пользовательское
обозначение), amsterdam — «Нидерланды» (186.246.45.246). Выбор отключает текущий VPN
и запускает проверенное committed resume; новые ACK/revision при переключении не
создаются. Native slots перед resume сверяются с подписанными профилями; неизвестный
шлюз и истёкшая конфигурация отклоняются. Resume не меняет профили/journal authority.
Ограничение первой версии: по одному подписанному профилю на transport slot; Россия
TCP REALITY, Нидерланды WG. NL AWG/TCP нужен для сетей с блокировкой WG.

Подготовлена новая неизменяемая версия0.1.5-beta06/code6; пока не установлена.
Локально Java/resources compilation +106 tests passed; CI и установка ожидаются.
Amsterdam phone peer .5 восстановлен в runtime и fcams.conf без expiry timer;
исходные3 peers сохранены, исходные сервисы не перезапускались. TCP8444 остаётся
running/unless-stopped. На телефоне пока beta05 и revision9. Далее CI beta06,
подписание проверенного APK, установка поверх Pilot без удаления данных, новая
revision>9 с обоими gateways, RU→NL→RU с проверкой трафика, сохранения выбора и lease.
Rollback сборки: новую версию не понижать с очисткой данных; при дефекте выпускать
следующий code/version. Рабочие endpoints после проверки не удалять.

## Восстановление пользовательского Pilot после cleanup — 2026-09-14

Причина обращения «не подключается VPN»: оператор завершил приёмку удалением
временного TCP8444 container, а установленная beta05 осталась с истёкшей revision8.
Это ошибка завершения пилота; рабочий доступ пользователю не был оставлен.
Восстановлен отдельный family-connect-android-tcp-pilot из сохранённой private
конфигурации, прежний pinned Xray image865c9e331170…, restart unless-stopped.
Config test passed, container running, внешний TCP185.251.89.19:8444 reachable,
expiry timer inactive. Исходные TCP443/API/AWG не изменялись.

Offline подписана и опубликована в существующий Reticulum relay revision9,
previous hash fdc106fed72d7ce6a3199fe3c2cfd96436abff1544122829142c74ab21348bd9,
envelope SHA256 b811d17b92e6d2750ce6a6adeb96f2c51e1e5bcec6d356e74b7a617b96f3c9d0.
Lease ограничен текущим entitlement: **15.09.2026 11:34:16UTC / 13:34:16 Brussels**.
Новая сборка не устанавливалась: Pilot0.1.4-beta05/code5/source8b6d51b.
CI текущего checkpoint1bad661: phase034846985307 tests/failover success.

После разрешённого пользователем Wi-Fi ADB TLS pairing подключён Redmi/joyeuse.
Через UI Pilot выполнено «Подключить через Reticulum»: проверены device-signed ACK9
RECEIVED/APPLIED1789391829, COMMITTED1789391831 (error NONE). UI подтверждает
«Туннель включён», «VPN отвечает», TCP REALITY и успешную проверку соединения.
Это подтверждает встроенный bound DNS/HTTPS health; отдельное числовое значение
внешнего IP в полученном UI dump не отображалось. После включения VPN mDNS ADB
пропал, прямое TLS ADB подключение восстановилось. VPN оставлен включённым.
Открыты наблюдение длительной работы и штатное продление entitlement/config до
истечения; не выдавать
lease более24h и не переносить offline signing key на сервер. Не удалять этот вход
по завершении диагностики. Следующий revision должен быть >9, previous hash — hash9.
Rollback: остановить только family-connect-android-tcp-pilot, сохранив private файлы
и journal; это отключит данный телефон и требует явного основания, повторно
не выполнять как обычную уборку теста. Для изменения конфигурации — новая revision.

## Android live acceptance и beta05 — 2026-09-14

На Redmi Note9 Pro/Android12 установлен **0.1.4-beta05/code5**, source8b6d51b,
com.familyconnect.app.pilot; исходный com.familyconnect.app0.1.0/code1 сохранён.
APK SHA256 e83c0841dfa3719e50bef3509fdb436ce7f2fb17c8479c556fa13d80d974d951,
постоянная offline beta signature,132 app unit/8 instrumentation и отдельный
storage restart5836→5870 passed. Clients34843986160, Android diagnostic34843986164,
phase034843986155 success. Публичного release/tag/catalog update не было.

На beta04 принята цепочка HTTPS IP enrollment → signed encrypted Reticulum → native
WG/AWG2/TCP → bound DNS/HTTPS → device-signed ACK, health rollback, crash после
APPLIED_PENDING с durable outbox/recovery и expiry stop/refusal. В beta05 добавлен
bound health retry в прежнем15s budget, устранены лишние UI text updates. После
обновления прежняя identity приняла revision8/COMMITTED;3/3 повторных TCP подключений
(два disconnect, один force-stop) подтвердили HTTPS IP185.251.89.19. Standard UI XML
получен, бесконечного idle wait нет. Revision8 истекла12:58:55UTC, VPN/services off.
Краткие прогоны не доказывают длительную устойчивость или все причины ранних отказов.

Телефон находится в Европе. Пользователь сообщает полную блокировку WG в России;
приёмка РФ требует AWG/TCP в российских сетях. Европейский WG остаётся baseline.
Открыты managed Auto/blocked-WG failover, AWG3.1 signed schema, relay/whole-gateway
outage, Doze/handover, полный routing/IPv6/DNS и длительная эксплуатация.

Временные Android WG/AWG peers удалены (исходные3/1 peers сверены), TCP8444 container
удалён, три expiry timers остановлены. Исходные API/AWG/TCP не перезапускались.
UI helper/XML и JDWP forwarding убраны; adb usb выполнен, Wi-Fi5555 connection refused.
Native identity/journal и private receipts сохранены. Для продолжения: новая revision>8,
previous hash fdc106fed72d7ce6a3199fe3c2cfd96436abff1544122829142c74ab21348bd9;
истёкшие тестовые конфигурации/удалённые endpoints не использовать как рабочий сервис.
Далее оставшиеся Android gates, Windows native Stage5 и остальные условия трёх
платформ. Django/платежи после VPN; messenger/iPhone отложены.
[Отчёт](releases/2026-09-14-android-storage-runtime.ru.md) ·
[Runbook](testing/android-stage5-live.ru.md) · [Sanitized receipt](android-stage5-live-result.json).

## HTTPS для Android регистрации — 2026-09-14

https://185.251.89.19:8443 развёрнут перед прежним localhost product API.
nginx1.30.4/Certbot5.4.0 pinned digests; публичный IP TLS expiry21.09.2026 02:18:22GMT.
Staging/production issuance, external TLS/routes/body/rate limits и renewal dry-run
passed; отдельный twice-daily timer active, ручной renew/reload success. Новые UFW
IPv4 TCP80/8443; прежний API и VPN не перезапускались. Созданы отдельные single-use
invitation/entitlement с предварительной private DB backup; Android enrollment выполнен
в beta04; дальнейшие live WG/AWG2/TCP/recovery описаны выше. Осталось
наблюдать scheduled certificate renewal. [Rollout/rollback и тесты](releases/2026-09-14-product-https.ru.md).

## Исторический checkpoint a342d4b и подготовка restart test — 2026-09-14

Для a342d4b Client builds34833797626: Linux/Windows/Android success;
Android diagnostic34833797792 success; phase034833797631: tests/failover success.
Release job skipped. Последний desktop release по API — v0.2.9; новый APK не
публиковался. Для новой установки подготовлена версия0.1.3-beta04/code4, debug package
com.familyconnect.app.pilot (Family Connect Pilot); beta03 не заменяется.
Добавлена обязательная проверка Android Keystore/AtomicFile/journal/outbox:
отдельные prepare → force-stop → recover процессы, отказ clock regression,
corrupt storage и повторной генерации identity. Java compilation и локальные
положительные/отрицательные проверки CI gate прошли. CI34836392940: все8 instrumentation
cases passed; дополнительный restart runner не нашёл удалённый Gradle test APK.
Добавлена установка уже собранной пары перед обеими фазами; повторный CI ожидается.
Телефон Redmi Note9 Pro/Android12 доступен, установлен0.1.0/code1. USB нестабилен;
подготовлен переход на локальный Wi-Fi ADB. Новая сборка пока не установлена.
Полная регистрация→RNS→native apply→Internet→ACK и crash rollback ещё не приняты.
Далее: новый runtime CI, подключение ADB и подписанная тестовая сборка, затем
полная Android-приёмка и остальные [условия трёх платформ](PLAN.md#release-gates-three-platforms).
[Отчёт и границы проверки](releases/2026-09-14-android-storage-runtime.ru.md).

## Git checkpoint и Android runtime acceptance — 2026-09-14

Накопленные исходники357 файлов сохранены коммитом af46e87 и отправлены в origin/main.
Client builds34828757268: Windows/Linux success, Android APK/unit/lint прошли;
эмулятор выявил устаревший Auto-тест, пытавшийся менять профиль при активном VPN.
Тест исправлен: проверяет запрет изменения и восстанавливает профиль после disconnect;
cleanup ждёт освобождения service owner. Добавлены APK gates для Python/RNS/bootstrap/
лицензий и обязательный результат ControlRnsRuntimeTest в обоих Android workflows.
Docker test stage теперь копирует Python carrier: локальная сборка passed,353 tests/27s.
Проверка runtime report принимает успешный RNS test, отвергает missing/skipped.
Повторный CI для исправлений ещё предстоит; полное live Android enrollment→relay→VPN→ACK
не проверено. Версия0.1.2-beta03/code3 сохранена, релиз и установка не выполнялись.
[Отчёт](releases/2026-09-14-git-android-acceptance.ru.md).

## Android Stage 5: автоматический RNS carrier и ACK — 2026-09-14

Добавлен явный запуск «Подключить через Reticulum»: встроенный RNS получает
challenge, Java подписывает proof ключом зарегистрированного устройства, получает
encrypted signed envelope и передаёт его существующему service owner/verifier/journal.
ACK отправляется из durable outbox; повтор обмена через60 секунд, недоступность relay
не выключает работающий VPN. TCP socket привязывается к underlying Android network.
Chaquopy16.1.0 / Python3.10 / RNS1.5.1 / pyserial3.5; добавлены лицензии и CI Python.
98 Java tests, два реальных loopback RNS сценария (включая internal crypto), aapt2/
Java compilation и Gradle Python assets packaging passed. Это ещё не полная APK-сборка
и не Android runtime acceptance. Версия остаётся0.1.2-beta03/code3, серверы не менялись.
Следующее: APK/native ABI и instrumentation на Android, публикация конфигурации именно
для зарегистрированного Android в ControlRelay, проверка minimum-version и живого
receive/apply/health/ACK/reconnect. Product enrollment сам не публикует envelope в relay.
[Отчёт, воспроизведение и оставшиеся проверки](releases/2026-09-14-android-control-rns.ru.md).

## Android Stage 5: explicit signed-file intake — 2026-09-14

MainActivity принимает encrypted signed envelope через отдельный системный picker,
проверяет лимит65536 bytes и запрашивает VPN permission. Non-exported service получает
снимок bytes, не URI/path; принимает файл только при остановленной сессии. Завершённая
регистрация/device binding проверяются перед существующим receive/apply/health/journal.
Cold duplicate committed проходит safe resume без перезаписи профилей; reject/rollback/
failed показываются отдельно. Pending bytes не сохраняются в instance state.
91 Java tests passed; aapt2 resources и app Java compilation passed с cached engines.
Это локальный ручной bootstrap, не автоматическая RNS/HTTP доставка. ACK остаются
в outbox. Android OS/UI/process-death/full Gradle/lint/ABI acceptance ещё не выполнена.
APK/версии/серверы не менялись. Далее runtime acceptance и RNS carrier/ACK delivery,
minimum-version policy и полный release plan.
[Проверки, применение и ограничения](releases/2026-09-14-android-control-intake.ru.md).

## Android Stage 5: explicit Reticulum enrollment — 2026-09-14

Добавлены UI регистрации, coordinator, отдельный encrypted enrollment state и HTTPS
adapter. Identity и пустой journal сохраняются до регистрации; RNS signature связывает
challenge и WG key. Повтор использует прежние identity/origin/proof; lost reply
проверяется через существующий provisioning challenge. Private keys/token не
сохраняются в enrollment metadata и не логируются; private keys остаются в device vault.
81 Java и57 Python tests passed; aapt2 resources и app Java compilation passed.
Это не Android Keystore/AtomicFile/UI/TLS/runtime/full Gradle/ABI acceptance. APK и
live enrollment не выполнялись. Не выдаётся и не применяется VPN config.
Далее native runtime acceptance, получение signed Stage5 config/RNS carrier,
ACK delivery и minimum-version policy; manual admission/managed Auto/AWG3.1 открыты.
[Порядок использования, ограничения и rollback](releases/2026-09-14-android-control-enrollment.ru.md).

## Android Stage 5: explicit committed resume — 2026-09-14

Явный connect после IDLE recovery теперь проверяет committed envelope на текущий
момент и поднимает только сохранённый профиль, точно совпадающий с signed config
и собственным WG key. Нет profile writes, новой revision или ACK при reconnect.
Проверяются traffic health, expiry/clock; ошибка останавливает engine. Pending сначала
восстанавливается, rollback не переходит к повторному resume/legacy/Auto.
63 Java tests passed; app Java compilation passed с Android35/cached engine/R.
Это не runtime/full Gradle/lint/APK acceptance. Далее explicit enrollment с RNS
identity/WG binding/init journal, Android runtime и carrier; текущий минимум версии
проверяется честно. VersionCode3/0.1.2-beta03, установка и серверы не менялись.
[Проверки и ограничения](releases/2026-09-14-android-control-resume.ru.md).

Пользователь запросил привязку клиента к криптографической identity Reticulum;
существующий proof/key binding сохраняется. Предложена схема Django/PostgreSQL
для кабинета/оплаты плюс Prometheus для технических метрик. Она документирована,
но ещё не реализована: [архитектура](design/django-product-plane.ru.md).

## Android Stage 5: восстановление при запуске службы — 2026-09-14

ConnectionService теперь проверяет managed state под существующим owner и запускает
journal recovery на том же worker до подключения. Pending откатывается; IDLE и
успешный rollback не переходят к legacy/Auto. Orphan files/keys и ошибки Keystore
не допускают обычное подключение; import/clear gate сохранён. Без явной команды
connect обычный WG больше не запускается. При отсутствии engine служба завершается.
50 Java tests passed (7 новых); компиляция app Java с Android35 и cached engine/R passed.
Это не Android runtime/full Gradle/lint/новый APK. Safe resume committed config,
explicit enrollment/identity+WG binding/init journal, admission ручных операций,
Keystore/AtomicFile/process-death/VPN acceptance и RNS carrier остаются впереди.
Версии, установка и серверы не менялись.
[Результат, проверки и возврат](releases/2026-09-14-android-control-startup.ru.md).

## Android Stage 5: native application adapter подготовлен — 2026-09-14

ControlApplication выполняет snapshot/apply/health/rollback над фиксированными
wg/awg/tcp slots; private WG key подставляется из device identity, прочие профили
сохраняются. Partial write/crash восстанавливает snapshot; отмена и expired lease
запрещают reconnect. ConnectionService содержит внутренний dispatcher через свой
worker/engine и точный owner; второй VPN lifecycle не создаётся. DNS+HTTPS health
привязан к VPN Network, добавлены cancellation/lease timers.
Trust anchor — packaged resource, побайтно равен desktop roots; version проверяется
по Android package version, без подмены0.2.9.43 Java tests passed, app Java compilation
passed с cached engine/R; Native runtime/full Gradle/lint пока не приняты.
Dispatcher ещё не вызывается из UI/Reticulum/startup; legacy managed-state gate
сохраняется. Следующий блок — startup recovery/enrollment и isolated Android
Keystore/AtomicFile/process-death/VPN acceptance. APK/версии/серверы не менялись.
[Реализация, проверки и ограничения](releases/2026-09-14-android-control-application.ru.md).

## Android Stage 5: владелец службы и профильных операций — 2026-09-14

ConnectionService удерживает отдельный owner от начала worker-сессии до успешного
engine.down/awaitShutdown и завершения destroy cleanup. Auto/health/stop callbacks
проверяют owner; старая служба не освобождает новую сессию. ProfileStore save/clear
согласованы с тем же owner, удаление вынесено из UI-потока. Control receive/recover
также отказывают при активном legacy owner; ACK flush остаётся независимым.
Connect/Import/Clear проверяют любые Stage5 files/base/bak/new и orphan aliases:
пока native recovery adapter не подключён, managed state блокирует legacy mutation,
а не обходится/удаляется. Это защитный gate, не готовое автоматическое восстановление.
33 Java tests passed; все текущие Java app sources скомпилированы с Android35 и
ранее собранными engine/R dependencies. Native runtime, full Gradle/lint и APK
не проверялись/не выпускались; один missing-annotation warning сохранён в отчёте.
Следующий блок: native recovery/application adapter через существующий service
lifecycle и isolated Android Keystore/AtomicFile/process-death acceptance.
[Изменения, проверки, ограничения и возврат](releases/2026-09-14-android-control-owner.ru.md).

## Android Stage 5: журнал и восстановление ядра — 2026-09-14

Добавлены ControlJournal/ControlTransaction, device-signed ACK и ограниченная очередь,
Keystore/AtomicFile adapter для отдельного зашифрованного журнала. Намерение записи
предшествует apply; commit и ACK сохраняются вместе. Pending после перезапуска
откатывается; floor не уменьшается. Ошибка rollback блокирует вход manual/receive.
Отправка ACK не удерживает общий owner и не теряет новые concurrent events.
JDK17 + Android35 compilation passed; **23 Java tests passed**, включая все16 шагов
трёх immutable Python transcripts, прежние30 configs/15 ACK/32 structural/4 cipher
refusals. Проверены сбои до/после записи, lease expiry, clock regression, повреждение
журнала и точные canonical ACK. Existing fixture manifest не изменён.

Это библиотечное ядро и скомпилированный OS adapter, ещё не Android runtime acceptance.
Activity/ConnectionService/ProfileStore пока не подключены к owner/journal;
production operation coordination не заявляется. Следующий блок: интеграция с
существующим service lifecycle и проверка Keystore/AtomicFile/process death, затем
native apply/health/rollback и RNS carrier. APK/серверы/версии не менялись.
[Отчёт, проверочные команды и возврат](releases/2026-09-14-android-control-journal.ru.md).

## Android Stage 5: identity сохранение подготовлено — 2026-09-13

По уточнению пользователя продолжена Android-часть Stage 5. Добавлены независимые
RNS/WG ключи, совместимый enrollment proof и отдельный AndroidKeyStore/AtomicFile
vault с явным create/load, запретом неявной смены identity и read-back после записи.
JDK17/Android35 compilation passed;8 Java tests и51 Python tests passed, включая
неизменённые conformance vectors и точное совпадение proof с Python reference.
Keystore/AtomicFile runtime ещё не проверен. Activity/service пока не подключены;
следующий блок — durable journal/outbox, общий operation owner и process-death
recovery, затем native apply/health/rollback и RNS carrier. APK/серверы/версии
не менялись. Предыдущие незакоммиченные изменения сохранены.
[Отчёт, проверки, ограничения и возврат](releases/2026-09-13-android-control-identity.ru.md).

## Android archive GIF renderer prepared — 2026-09-13

Full candidate archive49 GIF/374251 bytes added with SHA256 provenance;69 text
aliases, unchanged signed text, no image bytes on RNS. ChatSmileyTextView uses
bounded built-in GIF reads, up to8 animated occurrences, foreground/visibility
checks and callback cleanup. SDK35/JDK17 compilation and crypto/token checks passed;
Pillow verified every hash/frame/size. Actual Android rendering/lifecycle untested.
Exact official ICQ pack provenance/release rights still pending; no APK packaged.
No chat screen or RNS/Store bridge wired. Next: Android carrier/Store bridge and
Keystore/lifecycle runtime acceptance, then AWG3.1 signed schema and chat UI.
[Report, integration contract and rollback](releases/2026-09-13-android-icq-renderer.ru.md) ·
[49 animated samples](design/icq-animated-gallery.html).

## Android chat key foundation; exact classic ICQ smileys requested — 2026-09-13

Separate AndroidKeyStore wrapping alias and bounded61-byte AES-GCM Store-key file,
explicit create/load and fail-closed missing/corrupt state. SDK35 compilation and
JDK17 crypto/token checks passed; device Keystore/AtomicFile runtime untested.
User requires original animated ICQ2000s smileys. Custom drawing removed; archived
GIF samples available for visual comparison, exact provenance/version still pending.
Text-only2–3-byte tokens prepared; no image renderer/picker or Android RNS bridge yet.
No APK/server deployment. Next: original asset match and lifecycle-aware rendering,
RNS/Store bridge, runtime Keystore acceptance, versioned AWG3.1 signed schema.
[Report and boundaries](releases/2026-09-13-android-chat-foundation.ru.md) ·
[Animated reference preview](design/icq-classic-preview.html).

## Event-driven foreground mailbox sync — 2026-09-13

SyncController coalesces lifecycle/refresh events into one bounded worker and one
pending pull. No periodic polling or event-free retry. Foreground+online required;
background/network loss cancels, generation fence ignores late results.30s cooldown,
error backoff capped300s; close/join must finish before Store closes. Receive-only:
outbox and Android callbacks not wired. Real local RNS resume delivery/purge passed;
20 duplicate lifecycle events produced one attempt. Full suite51 passed/71.64s; final close refinement verified by10 sync tests/3.29s.
No server/APK changes. Next: Android carrier/Keystore/lifecycle integration and
versioned AWG3.1 signed configuration; push/hints, outbox and Doze remain open.
[API, tests, limits and rollback](releases/2026-09-13-messenger-event-sync.ru.md).

## Compact mailbox batch accepted — 2026-09-13

Mailbox.publish_many sends1–4 messages on one authenticated link with a shared
bounded deadline and individual durable ACKs. Partial failure/cancellation preserves
completed and queued messages; unchanged ciphertext retry/deduplication.42 messenger
tests passed (65.86s). Amsterdam four-message send: 4419 → 2373 RNS interface
bytes (46.30% reduction in this run); all8 messages delivered/purged.
Empty fetch and65s idle measured separately; not full TCP/IP or a capacity estimate.
No daemon/Android deployment or APK packaging. Next: event/resume-driven bounded
sync and adverse-link traffic/recovery, then Android carrier/Keystore/AWG3.1 schema.
[Measurements, reproduction, rollback and limits](releases/2026-09-13-messenger-compact.ru.md).

## Amsterdam mailbox live; compact messages remain a requirement — 2026-09-13

Dedicated closed RNS1.5.1/LXMF1.1.1 service on TCP4243 deployed for two diagnostic
identities. Offline delivery, volume/service restart persistence, commit-before-purge,
empty repeat fetch and reply passed live. Separate64MiB volume,192MiB memory ceiling;
actual post-test memory23.3MiB. Existing VPN/control services active; no APK packaged.
34 messenger tests passed (59.59s). Four-byte text:115-byte signed LXMF,208-byte
ciphertext; cold publish RNS interface counters855 TX/416 RX, excluding TCP/IP overhead.
Next: measure message-series/empty-fetch/idle budgets and reduce control exchanges
without weakening signatures/durable delivery; then Android carrier/Keystore/UI and
versioned AWG3.1 signed schema. Compact binary payloads are an explicit user requirement.
[Live evidence, bootstrap, rollout/rollback and limits](releases/2026-09-13-amsterdam-mailbox.ru.md).

## Closed messenger ingress and bounded spool — 2026-09-13

Authenticated Family Connect RNS put endpoint, closed sender/recipient allowlist,
pre-insert global/per-sender byte+count limits, rate limiting, FULL commit ACK and
stable encrypted retries. Native anonymous LXMF uploads/peering not registered;
closed ingress requires Mailbox.publish (not unmodified PROPAGATED clients).
SQLite file ceiling plus actual16MiB ext4 ENOSPC test passed: no false ACK,
previous message preserved, recovery/reopen successful. Combined521 passed/2 existing
warnings (58.46s), including31 messenger checks. No server/APK changes.
Next: dedicated bounded runtime volume and service/identity/bootstrap in Amsterdam;
Android RNS carrier plus versioned AWG3.1 signed schema for automatic conf delivery.
Linux signed conf delivery via Amsterdam RNS already has live acceptance; Android
currently uses manual AWG3.1 import. Chat remains separate from VPN control.
[Evidence, conf status and limits](releases/2026-09-13-closed-mailbox.ru.md).

## Offline messenger delivery and commit-before-purge — 2026-09-13

LXMF1.1.1/RNS1.5.1: explicit propagated send with relayed status; new bounded
Mailbox pull stores verified text before requesting node deletion. Fresh links,
trusted node public key, cancellation, duplicate-safe retry and download limits.
Three-process loopback acceptance passed: recipient offline, node restart, denied
fetch, injected storage failure preserving spool, retry, recipient restart/dedupe,
quota cleanup, aged-record expiry and explicit purge after durable commit.
Combined local suite516 passed/2 existing warnings (53.71s), including26 messenger
checks. No APK/version/server changes. Remaining: anonymous upload admission limits,
hard disk quotas and service lifecycle before Amsterdam; Android Keystore/UI,
automatic sync, application delivery ACK and TCP adverse-network measurements.
[Evidence and limitations](releases/2026-09-13-messenger-offline.ru.md).

## Transport reliability and messenger text core — 2026-09-13

User paused additional APK packaging; continue transport/messenger source work.
RNS1.5.1 adapter now waits for establishment callback after LRRTT send, not early
ACTIVE status. Deterministic old-code regression fails2/current passes2; real
control lifecycle/extracted preview pass. Previous CI timeout attribution remains
unproven. Linux TCP/WG/AWG health probes share8s budget and force interface names
(`if!`), avoiding hostname interpretation if the interface disappears.
Messenger prototype: LXMF1.1.1/RNS1.5.1, independent encrypted identity/contacts/
history/outbox, signed text, duplicate suppression, restart/manual retry and stale
callback fencing. Actual two-process DIRECT delivery/receipts pass; no Android UI,
Keystore, automatic retry scheduler or offline propagation service yet.
Local combined suite506 passed/2 existing warnings; Docker control350 passed.
No app/server deployment or APK version change. Source commit intentionally uses
[skip ci] to prevent existing workflows packaging clients; new messenger-only
workflow added, remote CI not claimed. Next: isolated offline propagation acceptance,
key/lifecycle integration for Android, TCP adverse-network runtime measurements.
[Evidence and limits](releases/2026-09-13-transports-messenger.ru.md) ·
[Prototype](../messenger/README.ru.md).

## Android beta03 health feedback accepted in emulator — 2026-09-13

Source6383130: manual VPN-bound DNS health feedback, session-bound public-IP
HTTPS checks and stale-result refusal. Manual probe failures retain the tunnel.
Client CI34776015693 Android/Linux/Windows success;JVM30+lint,6 instrumentation
cases including screen-off5s,≥20s UDP outage/recovery, terminal Disconnect and
new session IDs passed. ARM64 beta03/code3 signed with existing beta key,
51,154,127bytes;v2/v3/alignment/payload verified. Existing beta02 profile reused.
User postponed Russian-phone tests while in Ghent: physical5min sleep, Doze,
battery and Wi-Fi/mobile handover remain open. No server/profile changes.
Separate phase0 failover build failed on extracted-preview RNS initial challenge
timeout;local focused2 tests passed, root cause not fixed. Next: diagnose RNS
startup/request intermittency and later physical Android checks.
[Beta03 instructions](testing/android-beta03.ru.md) · [Evidence/CI limits](releases/2026-09-13-android-stability.ru.md).

## Android beta02 calls reported working; load checked — 2026-09-13

User reports AWG3.1 working on MTS Vladikavkaz and home Rostelecom, WhatsApp and
Telegram calls with clear uninterrupted audio. Current20s idle measurement: host
CPU0.301%, AWG0.0161%, AWG RAM7.16MiB/peak15.63MiB, available RAM720MiB, restarts0.
Historical sysstat resolution10min. User clarified call times19:07/19:17 were
apparently Brussels time, i.e.20:07/20:17MSK: matching intervals show host CPU0.53%
and1.56%, with VPN activity. These are whole-host10min means, not per-call peaks.
No server upgrade indicated for the current small pilot; concurrency untested.
Next: synchronized call measurement if needed, screen sleep and network handover.
[Evidence and limits](releases/2026-09-13-android-calls-load.ru.md).

## Android AWG3.1 beta02 ready for first phone — 2026-09-13

Source d0709bc: Android CI34768083248/job103752559759 passed native4ABI build,
JVM30+lint and5 emulator runtime tests. Engine b5928ef + S4 patch, manual HPK/
content padding/trailers/cookies fields; custom timings and signed control3.1 unsupported.
ARM64 APK0.1.1-beta02/code2 packaged from accepted payload,51,154,127bytes, signed
with the same beta01 key; v2/v3/alignment/hash verified. Remains a debug technical pilot.
Separate Amsterdam AWG3.1 UDP443/fcawg31 service active+enabled. DNS/HTTPS(NL),
1MiB download, reconnect and namespace cleanup passed. Existing WG/RNS preserved.
Python485 passed/2 warnings. Phone/WhatsApp acceptance still pending; no claim of
DPI resistance in the user's network. Next: install over beta01, Auto off, import new
AWG profile, verify IP/sites/messages/calls, then sleep/handover.
[Phone instructions](testing/android-beta02-awg31.ru.md) · [Evidence and rollback](releases/2026-09-13-android-awg31.ru.md).

## Android-first technical beta01 prepared — 2026-09-13

User selected Android for initial testers. Accepted CI34758085225 APK downloaded;
archive matched official GitHub digest, all4 ABI hashes/licenses/fixture exclusion
checked. Local persistent beta signing key created; final APK v2/v3 verified,
only signing META-INF changed. APK0.1.0/code1 debug, not a mass-release build.
Separate Amsterdam WG peer10.79.0.4/fd79:92::4 prepared; prior peers preserved,
no server restart. DNS/HTTPS(NL)/download/reconnect passed in Linux namespace.
Physical Android install/network not yet tested: next gate is one real phone,
then sleep/handover/device matrix before expanding testers. AWG3.1/recovery is
not in this APK; Reticulum native onboarding still pending. No public release.
[Tester steps](testing/android-beta01.ru.md) · [Hashes, signing and rollback](releases/2026-09-13-android-beta01.ru.md).

## AWG3.1 managed recovery prototype — 2026-09-13

Three isolated repeats recovered server restart in3.7529/3.7665/3.7531s vs previous
~16.1s automatic recovery. One pinned-profile reset each; healthy controls zero resets.
Policy:3 consecutive failed probes, at most2 resets/invocation,10s cooldown,20s
observation budget checked between callbacks; stop on cancellation/ownership loss.
Focused7, full Python485 and Docker test-stage348 passed. No client/server deployment.
Linux control CI passed; initial phase0 failover image-build failure retained (logs403).
One retry34761940493 on unchanged code passed tests+failover; cleanup verified.
Production broker lease/revision/expiry/disconnect integration remains the next step;
H4 recovery,1CPU/PMTU/long-run and Amsterdam AWG acceptance remain open.
[Measurements and limitations](releases/2026-09-13-awg31-managed-recovery.ru.md).
[Own transport roadmap](own-transport-roadmap.ru.md): current RNS1.5.1 dependency is
confirmed; an independent Reticulum replacement/new VPN wire protocol is a goal,
not an implemented result. Existing control/journal work remains the foundation.

## AWG3.1 adverse-condition experiment — 2026-09-13

Experiment2 adds strict u16 tools parsing: reject65536 instead of truncation;
12 negative C cases and valid boundary ranges passed, selected engine suite count=3.
Three live virtual repeats passed wrong HPK/H4, invalid S1/padding, tunnel MTU,
1% configured loss with1MiB integrity, brief blackhole, link cycle, server restart,
and accelerated5s rekey. H4 recovery~15.1s and server restart~16.1s remain slow;
original15s failure retained.30s observation acceptance is not a reconnect fix.
Python478 passed; full upstream Outline remains unresolved. No deployment/app update.
Source c2bbd9a: phase0 CI34761027324 tests+failover passed; ordinary4-case sanity
also passed, namespace/IPC cleanup verified.
Next: managed recovery,1CPU load and path-MTU/long-run checks, then Amsterdam AWG.
[Evidence and limitations](releases/2026-09-13-awg31-resilience.ru.md).
[Reticulum/LXMF messenger proposal](reticulum-messenger.ru.md) documented; no messenger
code/service deployed. Messaging identity/history/lifecycle must be separate from VPN.

## AWG3.1 isolated experiment accepted within limits — 2026-09-13

Pinned engine v3.1.20260828 b5928ef + tools v3.1.20260812 ee0f0a9.
Unmodified device tests failed: first packets lost with S4 startup configuration.
Local explicit patch refreshes padding after blocked TUN Read; original device
and five new first-packet cases passed in the selected suite count=3.
Full go test ./... still fails Outline external integration; no full-suite claim.
WG/base/padding/trailers virtual comparison:12/12 runs,96MiB, zero measured ping
loss; AWG ~16.4Mbps on shaped20Mbps/~70ms RTT. Trailers cost ~6.4% more link bytes
than AWG base here; no DPI or VPS-capacity acceptance. Both engines RSS <14.59MiB
at sampled transfer end, not peak/service budget. No server/app/catalog/main change.
Source b90e39a: phase0 CI34759917018 tests+failover passed; local Python478 passed.
Next: negative profiles and loss/MTU/reconnect/rekey checks,1CPU load, then separate
Amsterdam AWG pilot; schema3.1 and Windows/Android migration remain open.
[Recipe, regression, metrics and limitations](releases/2026-09-13-awg31-experiment.ru.md).

## Managed Linux control route accepted — 2026-09-13

Source7ad40c0: once --managed-route leases a root-pinned UID/TCP relay route,
cleans it after exchange/client death, and recovers broker crash intent on next use.
Root helper/pin/Polkit installed locally; desktop current remains0.2.8.
GUI/control entry contention waits at most5s without bypassing journal ownership.
478 tests passed. Isolated kernel lifecycle/uplink tests and host client-SIGKILL
cleanup passed. Real canonical launcher revision7 + active-VPN duplicate + GTK/HTTPS
+ signed ACKs passed without manual rule. Initial two unexplained OPERATION failures
retained; physical handover/suspend/long-run tests remain open.
Final VPN off, rules removed, journalIDLE/floor7/committed7/outbox0.
Linux preview CI hash matched; AWG/TCP/Linux/Windows passed. Docker test-stage COPY
fixed in0136c54; repeated phase0 tests+failover passed. Android CI103725874969 also passed (checked13.09).
Next: AWG3.1 compatibility/runtime/profile migration and separate Amsterdam pilot;
3.1 is still rejected until implemented. [Initial upstream/schema audit](awg31-migration.ru.md) started.
No release/catalog/main update.
[Version hashes, expiry, evidence and rollback](releases/2026-09-13-managed-control-route.ru.md).


## External Reticulum pilot accepted with operator route — 2026-09-13

Amsterdam186.246.45.246:4242 now serves the pinned trusted RNS relay as fc-relay,
active+enabled; same VPS as WG, not independent infrastructure. Existing device
identity/journal preserved, second WG peer10.79.0.3 added; manual peer.2 preserved.
Revision4 committed but lost ACK connectivity after full VPN; outbox3 retained.
With temporary TCP4242→main policy rule, revision5 committed, all6 signed ACKs
arrived, duplicate delivery made no new profile; real GTK and bound HTTPS confirmedNL.
Relay restart preserved identity/configs/ACKs and duplicate fetch passed with VPN off.
Final: VPN off, temporary rule removed, journalIDLE/floor5/committed5/outbox0.
Next priority: managed trusted-relay route lifecycle in Linux runtime/helper, then
repeat without manual operator rule. Current installed0.2.8 unchanged; not a release.
Native protected state and independent infrastructure/alternate transport remain open.
[Evidence, exact lease expiry, limitations and rollback](releases/2026-09-13-external-reticulum.ru.md).


## Amsterdam paired Linux GUI pilot passed — 2026-09-13

Accepted preview66152538ee2a4f3e completed two real GTK Connect → Check IP →
Disconnect cycles: UI and interface-bound HTTPS both confirmed186.246.45.246/NL.
Profile fc-app-Amsterdam-pilot retained inactive, autoconnect=no. Host rules/default
routes/resolver/active connections restored; pending marker clear; GUI closed.
Import used app backend: native file chooser automation timed out. A harness profile
naming mistake was corrected; both preliminary failures retained in the receipt.
Installed0.2.8 unchanged; no server/release/catalog updates in this step.
Next: external trusted Reticulum relay and signed Amsterdam configuration delivery,
with peer/device identity binding and existing anti-replay state preserved.
[GUI evidence, limitations and rollback](releases/2026-09-13-amsterdam-gui.ru.md).


## Amsterdam real-network pilot passed — 2026-09-13

User authorized new empty VPS186.246.45.246: Ubuntu26.04,1 vCPU,955MiB RAM.
Native WireGuard UDP51820/MTU1280 installed, one locally generated client peer;
server key generated on-server. Service active+enabled, scoped nftables NAT/filter.
Final isolated Linux netns run passed DNS, two HTTPS egress checks (IP186.246.45.246,
countryNL),1MiB download, private-network/IPv6 refusal, server service restart and
full client reconnect. Server rekey readiness16.615s; host routes/rules/DNS unchanged.
Two preliminary failures retained: HTTPS immediately after server restart, then DNS
failure after bare client link down/up. Bare link toggle remains unaccepted; final
scenario recreates the complete connection. Not a fix/closure of TD-1 stability debt.
SSH key access verified; mandatory initial password change handled outside Git.
Private profile retained in ignored state-enroll/amsterdam-pilot, not imported in GUI.
Next: Amsterdam profile in paired Linux application, then external trusted Reticulum
relay and alternate transport checks. Native Windows/Android protected state remains.
Python462 and operator-script syntax checks passed.
No existing gateway/client install/catalog/main changes; Stage6 only partially begun.
[Deployment, evidence and rollback](releases/2026-09-13-amsterdam-pilot.ru.md).

## Android Stage5 verifier accepted — 2026-09-13

Source24159206a661bc7cea31a8f19d7c57c19f5796a1: Java schema2 configuration/ACK
verifier, pinned BC1.85.2/Gson2.13.2 with APK licenses. Local JVM:30 configurations,
15 ACK,32 structure+4 authenticated-cipher+12 JSON/UTF8 refusals passed; Python462.
Clients34750425107: linux:success, android:success, windows:success, release:skipped.
Phase034750425189 passed. Android runtime acceptance: True.
Manifest SHA256 c97e00ccff7440b09a636a792557c0602aba5eb63815cdc8fefe7755711ac3cd.
Fixtures confined to test assets; APK gate checks their absence and dependency licenses.
Next: protected Windows identity/journal/outbox and shared broker ownership, then
Android protected state. Native transcripts/carrier/VPN apply remain unimplemented.
No release/install/catalog/server/main changes; Android0.1.0/code1 unchanged.
[Implementation and CI receipts](releases/2026-09-13-android-control.ru.md).

## Windows Stage5 verifier accepted — 2026-09-13

Source38b055431758e3f2b80de1adfbf9df04cb299fcb (implementation581f83f): native
C# schema2 configuration/ACK verifier. Windows CI34749302222/job103702791743
passed30 configurations+15 ACK and31 extra structure refusals plus legacy checks.
Manifest SHA256 c97e00ccff7440b09a636a792557c0602aba5eb63815cdc8fefe7755711ac3cd
confirmed by Windows annotation. Local .NET and Python462 passed; phase034749302284
passed. Clients34749302204: linux:success, android:success, windows:success, release:skipped.
First CI had five startup_failure runs before jobs; GitHub unexpected error recorded.
AWG/TCP/Linux-control original runs did not execute; no new acceptance claim for them.
Next: Android verifier, then protected Windows identity/journal/outbox and broker
ownership. Native transcripts/carrier/VPN apply remain unimplemented.
No release/install/catalog/server/main changes; desktop0.2.9, installed Linux0.2.8.
[Implementation and CI receipts](releases/2026-09-13-windows-control.ru.md).

## Stage5 conformance corpus accepted — 2026-09-13

Source598454bad71fdf290a673c0f10a7f4afa61e2b18: immutable PUBLIC TEST ONLY
30 configuration inputs,15 ACK inputs,3 transcripts/16 steps.50 vector checks,
full local462 Python passed. Linux control34748501643 and phase034748501640 passed.
CI vector manifest digest matches committed corpus; paired archive digest unchanged
from the accepted live Linux bundle.48 corpus files preserve bytes under autocrlf=true.
Generator refuses overwrite and has no key-file inputs. No runtime/client/server changes.
Next: Windows native verifier against these exact bytes, then Android verifier and
protected identity/journal/ownership. Native Stage5 not implemented by this corpus.
[Conformance acceptance](releases/2026-09-13-control-vectors.ru.md) ·
[Portable fixture format](../tests/vectors/README.md).

## Linux health CI and Android diagnostic rerun — 2026-09-13

Health source d7c3d79: Linux control34747139792, phase034747139671,
AWG34747139717 and TCP34747139660 passed. CI archive SHA256 matches the live bundle.
Initial Clients34747139704: Windows/Linux passed, Android emulator failed; raw logs
API403, precise cause unavailable. This failure remains recorded, not erased.
Diagnostic-only source9092594 adds bounded JUnit annotations and scoped Android CI,
without app/test/timeouts changes. Android34747632083, Clients34747632066
(Windows/Linux/Android) and phase034747632071 passed. Initial transient cause unproven.
All public pilot reports and final CI receipts documented in the acceptance branch.
Next: native Stage5 interop vectors, protected identity/journal/outbox and shared
ownership; Windows broker first, then Android service. No native Stage5 implementation
claim, release/main merge/install/server changes. TD-1, AWG3.1 and Stage6 remain open.
[CI evidence](releases/2026-09-13-linux-control-ci.ru.md) · [Native plan](stage5-native-binding.ru.md).

## Linux paired live pilot passed — 2026-09-13

Corrected bundle66152538ee2a4f3e passed real RNS config2 apply/ACK, GTK selection,
interface-bound HTTPS gateway egress and DNS. Config3 process death after actual
apply preserved pending ownership; recover restored config2 and HTTPS. Duplicate3
returned ROLLED_BACK with ACK delivery; real GUI Disconnect/close and exact IPv4/6
policy-rule cleanup passed. Final journal IDLE/floor3/committed2/outbox0; pending=null.
Three pilot imports now retained inactive; installed Linux0.2.8 unchanged.
Packet metadata disproved the earlier inference of TCP setup failure: handshake and
client payload reached gateway; large response ranges failed to reach the laptop.
MTU1280 worked and was signed into config2/3, but restored1420 also passed once:
location/cause of size-sensitive loss and long-term stability remain unproven (TD-1).
Local412 tests and corrected package manifest previously passed; no new remote CI,
release, install or server mutation. Next: scoped CI for the health correction, then
native Windows/Android Stage5 binding. Local relay does not close independent Stage6.
[Packet evidence and live acceptance](releases/2026-09-13-linux-control-pilot-pass.ru.md).

## Live Linux pilot: traffic gate correction — 2026-09-13

Real RNS config1 applied, ACK delivered and paired GTK selected the active imported
WG profile. Independent bound HTTPS then failed; pilot stopped before crash recovery.
Bounded diagnosis: direct IPv4 HTTPS passed; both default/IPv4 TUN HTTPS timed out
before TCP connect, interface DNS passed. Cause is not established.
Cleanup passed: all VPN inactive, existing profiles preserved, IPv4/IPv6 policy rules
restored. One inactive pilot import retained. Journal IDLE/floor1/committed revision1:
old active-only health caused this commit; do not treat it as network acceptance.
Fixed control WG health to require interface-bound HTTPS/expected gateway egress
before candidate selection and commit. Local412 Python passed (including extracted
package); new bundle66152538ee2a4f3e manifest verified. No remote CI/release/install.
Next: request-to-flow diagnosis of WG HTTPS, then corrected bundle live acceptance
and crash/rollback/GUI return. Never reuse old accepted preview for live config apply.
Keep permanent identity/journal and issue higher revisions; no state reset.
[Live result, fix and limits](releases/2026-09-13-linux-control-live.ru.md).

## Registered Linux control pilot — 2026-09-13

User requested preparation of the permanent registration and trusted relay.
Prepared private `state-enroll/control-linux-pilot`: permanent device/relay identities,
real API enrollment, explicit local RNS configs, journal and offline-signed envelope1.
Real two-process RNS delivery with the extracted accepted bundle passed; signature,
device binding and byte equality verified. Journal remains IDLE/floor0; no VPN apply.
One isolated gateway peer10.77.0.252/32 installed by the periodic worker; three prior
WG peers preserved. Gateway lease expires 2026-09-13T08:43:59+00:00;
envelope expires 2026-09-13T08:40:14+00:00. Registration is retained for reuse.
Relay was stopped after the check. Local relay is not Stage6 independent ingress.
Next: bounded paired GUI/control apply, independent traffic health, recovery/return.
If expired, renew the gateway lease and issue/publish a higher signed revision using
the same identity/journal; never reset state. Native Windows/Android binding follows.
[Preparation and evidence](releases/2026-09-13-linux-control-resume.ru.md).

## Paired preview acceptance — 2026-09-13

Local409 Python passed, including66 extracted protocol/arbiter scenarios. Scoped
Linux CI34722755860 passed on247d16b; Docker272 tests and full phase034722963403
passed on3a28be7. CI tar.gz SHA256 matches the local preview. Previous Clients
Windows/Linux/Android all passed. Added local-only recover CLI, retaining ACKs
and pending state on failure. Manual paired pilot/return plan prepared.
Observed installed Linux **0.2.8**, previous0.2.7; old GUI has no arbiter. No
installation, profile mutation, release, catalog update or server changes.
Next: separate-directory manual paired preview pilot, then native Stage5 binding.
AWG3.1, TD-1 and Stage6 remain open.
[Acceptance evidence](releases/2026-09-13-linux-control-acceptance.ru.md) ·
[Manual rollout/return](linux-control-preview-rollout.ru.md).


## Paired Linux control preview — 2026-09-12

Operator GUI/core bundle added with an explicit public-file allowlist, integrity
manifest, runtime-only pinned dependencies and extracted launcher. Legacy six-file
desktop archive unchanged. Local405 Python passed; extracted real RNS lifecycle
and GTK smoke passed. Scoped Linux control CI34720569558 passed on source d8aef8a.
AWG/TCP pilot passed. Docker test-stage dependency omission reproduced and fixed
in ac6a22f: complete public desktop bundle + VERSION copied into tests stage only.
Local Docker250 tests passed; phase0 run34720868247 fully passed including build,
failover/auth/offline/revocation/cleanup and Python/Rust. Clients Windows/Linux
passed; Android subsequently passed (see 13.09 acceptance above).
[Docker fix evidence](releases/2026-09-12-control-docker-fix.ru.md).
No release/install/catalog/server changes. CI acceptance completed; manual paired pilot next; native Windows/Android binding, AWG3.1 and TD-1 remain open.
[Preview checkpoint](releases/2026-09-12-control-preview.ru.md).


Updated:2026-09-12. Desktop **0.2.9 published**, source `42f9d32`.
Linux/Windows release assets checked; signed update catalog sequence8 published in7650f32 and verified at the canonical URL. Linux **0.2.8 observed installed on13.09**; Windows last reported0.2.7.
No device installation performed. Server **0.2.1**, deployment source8cd0f2d/server
checkout117611c; TCP component **0.1.0** unchanged.

## Short matched HTTPS diagnosis — 2026-09-12

Two bounded same-destination direct/TUN runs passed: Python verified TLS/HTTP1.1
6/6 direct +6/6 TUN; curl default ALPN/HTTP2 with original3s/5s budgets also6/6+6/6.
24/24 requests total, pinned IPv4 targets, sequential alternating pairs. Both runs
verified independent direct routing/egress, TUN egress and complete cleanup.
Curl median total: direct0.207s, TUN0.577s; TUN TLS completion0.343–0.472s.
Previous HTTPS4/6 timeouts did not reproduce. No causal fix, timeout/profile/binary/
server changes, packet capture or load campaign. TD-1 stability remains open;
no physical blocking/Stage6 resilience claim. Next development: coordinated Stage5
GUI/core packaging and scoped CI; capture request-to-flow evidence on a failing
bounded network run before changing transport settings. [Matched HTTPS result](releases/2026-09-12-matched-https.ru.md).

## Stage 5 Linux GUI coordination — local acceptance

Shared nonblocking process/thread arbiter added to Linux GUI and control apply/recovery.
Durable pending ownership survives process death and blocks GUI mutations until the
same journal recovers. Generation checks reject stale automatic recovery and refresh
GUI selection after a control commit; automatic recovery preserves its retry budget.
402 Python tests, GTK recovery, interaction checks and all 24 GTK layouts passed.
Six-file archive preserved; no application/helper installation, release or remote CI.
Older installed GUI does not participate; coordinated rollout of GUI/core remains required.
User authorized short network tests after GUI work: resumed on existing installed TCP.
Ready-TUN run: correct endpoint bypass/public routing, DNS3/3, HTTPS4/6 (two timeouts),
all cleanup assertions passed. Initial harness raced Type=simple startup; fixed readiness
wait before rerun. Network stability debt remains open; no long load/device campaign.
[GUI coordination and short network checkpoint](releases/2026-09-12-control-gui-network.ru.md).

## Stage 5 reference control core — local acceptance, 2026-09-12

Verified Reticulum delivery + transactional stage/apply/health/commit/rollback/ACK
implemented in a carrier-independent Python core with an existing Linux backend
boundary. 381 Python tests passed (56 new), including actual two-process loopback
RNS delivery, commit/ACK, failed health/rollback/ACK and duplicate safety. No HTTP
service required. Existing offline Ed25519 root reused; catalog sequence8 untouched.
AWG3.1 is explicitly versioned and rejected by the current capability before apply;
runtime migration remains TD-2. TD-1 device/load/full-routing remains deferred.
No commit, remote CI, native packaging, release, installation or server mutation.
Next: common GUI operation ownership/native binding and scoped CI before background
rollout. Independent control entry and alternate gateway remain Stage6.
[Stage 5 checkpoint](releases/2026-09-12-reticulum-control.ru.md) · [Architecture](stage5-architecture.ru.md).

## Android Auto — accepted in isolated CI, 2026-09-12

Application sourcea51aa52, accepted tests6fa2bc7. Clients34679094884 and
phase034679094921 passed: four ABI,23 unit methods,lint0 errors/10 warnings,3 API35 x86_64 instrumentation
methods. Auto: blocked WG→AWG, live AWG health loss→TCP, WG priority, missing WG,
finite exhaustion, startup cancellation, system revoke;12 UDP,6 REALITY HTTP,
1 OS resolver call,5 cleanup scenarios. Full regression:48 UDP,24 HTTP,4 OS DNS,
18 cleanup scenarios. Local Python325 passed. APK/native hashes verified.
VPN-bound DNS reachability uses two endpoints; HTTPS/general Internet availability
is outside this health criterion. One pass WG→AWG→TCP, cleanup before transitions.
[Report](releases/2026-09-12-android-auto.ru.md). No release/install/server changes.
Next implementation: stage5 Reticulum. Device/full-routing/sleep/handover remain deferred.

## Android TCP — accepted in isolated CI, 2026-09-12

Application sourcef42afb5, accepted test source8d748f5. Clients34676190826 and
phase034676190780 passed. Four ABI build,18 unit methods,lint0 errors/7 warnings;
API35 x86_64:18 REALITY HTTP (9 IPv4/9 IPv6),3 OS resolver calls,36 WG/AWG UDP,
13 cleanup scenarios across two instrumentation methods. Downloaded APK/native
hashes and absence of test helpers verified. Python325 passed.
One Go runtime, protected endpoint-only dialer, separate encrypted TCP profile,
explicit selector and VpnService lifecycle. [Report](releases/2026-09-12-android-tcp.ru.md).
Android0.1.0/versionCode1, no release/install/server/device changes.
Auto accepted in the checkpoint above; next stage5 Reticulum. External gateway, phone,
other ABI runtime, sleep/Doze/handover/health remain unaccepted; user tests deferred.

## Latest accepted Android WG/AWG checkpoint — 2026-09-12

Android WG/AWG accepted in API35 x86_64 emulator: 24 encrypted IPv4/IPv6 UDP
exchanges, 4 normal stops, pending cancellation and real system VPN permission
handover/revocation; separate encrypted stores preserved. One native Go runtime
replaces the crashing dual-runtime design. Application sourceba6ec3e, test sourcea93558a.
Clients34660308853: four ABI build, 12 unit methods, lint0 errors/7 warnings,
emulator passed; downloaded APK/native hashes checked. Phase034660308767 and
Python325 passed. [Report](releases/2026-09-12-android-awg.ru.md).
Android0.1.0/versionCode1; no APK release/install, no server/device change.
TCP accepted in the checkpoint above. Auto accepted above; next implementation stage5 Reticulum. External gateway,
phone/other ABI runtime, sleep/handover remain unaccepted; user tests still deferred.

## Latest accepted Windows checkpoint — 2026-09-12

- Windows Auto WG→AWG→TCP implemented: bound initial/ongoing health, SID ownership,
  cleanup before transitions, cancellation and SCM recovery. Source `1e13c74` accepted:
  clients 34654036404 (672 layouts/install/uninstall), AWG/Auto 34654036463
  (4 automatic scenarios, 6 UDP then 6 HTTP), TCP 34654036431 (84 HTTP/14 DNS/10 cleanup),
  phase0 34654036425. Python 325 and 7 C# policy scenarios passed; downloaded hashes verified. [Report](releases/2026-09-12-windows-auto.ru.md).
  No release/device/server changes. Next implementation: Android AWG/TCP, then stage5 Reticulum.

### Previous accepted AWG checkpoint

- Windows AWG signed profile/DPAPI, broker session/shared recovery, installer and UI
  implemented after native engine acceptance12/12 in CI34648502108/source29f8f27.
  325 Python tests passed. Clients 34652500879: 504 layouts/install/uninstall;
  AWG 34652500922: native 12/12 + LocalSystem 24/24 UDP,4 cleanup.
  TCP regression 34650231930: 84 HTTP/14 DNS/10 cleanup; phase0 34652500921 passed.
  App source ad30827; CI fixture fix 53fe266. Downloaded hashes verified.
  Explicit transport switching only; automatic WG→AWG→TCP remains next.
  No release/device/gateway changes. [Integration report](releases/2026-09-11-windows-awg-integration.ru.md).

### AWG engine foundation

- Windows AWG worker prepared from pinned amneziawg-go with stdin-only config,
  fresh Wintun, bound IPv4 outer UDP and no UAPI listener; native CI34648502108
  accepted12/12 UDP exchanges,4 negative probes and4 cleanup scenarios.
  Subsequent broker/profile/GUI integration is tracked above; no rollout.
  [AWG engine report](releases/2026-09-11-windows-awg-engine.ru.md).

### Earlier TCP health checkpoint

- Windows TCP bound health monitoring implemented: two targets, two failed cycles,
  shared bounded recovery, in-flight cancellation before cleanup. Source9863427 passed
  clients34646258699 (336 layouts), native/session34646258684 (84/84 HTTP,
  14 DNS, 10 cleanup scenarios) and phase0 34646258740. Downloaded hashes verified.
  External REALITY/full routing/production probes remain unaccepted; no rollout.
  [Health report](releases/2026-09-11-windows-tcp-health.ru.md).

### Earlier recovery checkpoint

- Windows TCP engine-crash recovery implemented: three retries after successful cleanup,
  15/30/60s backoff, SID ownership retained, cancellation/service stop prevents reconnect,
  exhausted budget visible in UI. Source7de6e69 passed clients34643426316 (336 layouts),
  native/session34643426300 (66/66 HTTP, 11 DNS, 8 cleanup scenarios), phase0 34643426354.
  Downloaded artifact hashes verified; no release/device/server change.
  Health monitoring/external REALITY/full routing still pending.
  [Recovery report](releases/2026-09-11-windows-tcp-recovery.ru.md).

### Earlier packaging/UI checkpoint

- Windows TCP packaging/UI implemented: pinned engine bundled with licenses/hash checks,
  WG/TCP selection, separate activation, TCP-only connect, pending cancellation and
  asynchronous error visibility. Platform runtime CI34641891335 passed (288 layouts, installed payload/broker/uninstall);
  native/session34641891317 and phase0 34641891414 passed, source34a3211.
  Downloaded installer hash verified; no release/device/server change.
  [Packaging and UI report](releases/2026-09-11-windows-tcp-ui.ru.md).

### Earlier broker session checkpoint

- Windows TCP broker network session implemented9f32b0c, accepted with harness6d207a2.
  Async connect/cancel, SID ownership, own IPv4/IPv6 routes/DNS/NRPT, durable journal,
  engine-exit cleanup and SCM restart recovery. Actual LocalSystem scoped CI passed
  24/24 IPv4/IPv6 HTTP,4 OS DNS checks, other-user refusals and5 cleanup scenarios;
  prior native lifecycle18/18 retained. Native/session CI34639769072, phase0
  CI34639769135 and implementation platform CI34639148397 passed. Downloaded hashes verified.
  Test account setup changed from PowerShell to direct WinAPI; password stays in memory.
  Full external REALITY/default-route path not accepted here; CI uses scoped routes/domain.
  Normal installer has no tcp engine directory and GUI has no TCP control yet. Next:
  packaging/UI/recovery, full-routing acceptance before distribution, then Windows AWG.
  No release/device/server changes; Android then Reticulum and deferred user tests retained.
  [Complete session evidence](releases/2026-09-11-windows-tcp-session.ru.md) ·
  [Operations and limits](windows-tcp-session.ru.md).

### Earlier process lifetime checkpoint

- Windows TCP process lifetime primitive completed, sourcedc8df7d. Pinned binary checks,
  kill-on-close Job Object, stdin-only config after job assignment, unexpected-exit
  observation. Native CI34637235553 passed18/18 local TUN/VLESS requests across explicit
  stop, owner crash and engine crash; no orphan process/adapter, routes/DNS preserved.
  Both binary tamper cases refused. Wintun first-install Windows environment defect fixed.
  Client CI34637235600 all platforms and phase0 CI34637235589 passed; downloaded hashes
  reverified. Actual owner is isolated CI harness, not broker/SCM; TCP connect still
  unexposed. Next: broker network session/routes/DNS + crash/restart cleanup, then UI/AWG.
  No release/device/server change; Android then Reticulum order and deferred tests retained.
  [Lifecycle evidence](releases/2026-09-11-windows-tcp-lifecycle.ru.md).

### Earlier Windows profile checkpoint

- Windows TCP signed profile/broker storage completed, source4ba46e1. Strict device-bound
  Ed25519 grant, sequence floor, atomic LocalSystem DPAPI storage and offline issuer.
  300 Python tests; C# shared fixture/config +29 rejection checks; actual installed
  Windows broker18 checks passed. Client CI34633788708 all platforms and phase0
  CI34633788755 passed. Docker test-stage dependency and test-client ValueTask wait fixed.
  No release/device/server change. TCP connect remains unimplemented in broker/GUI;
  next lifecycle/routes/DNS, then UI/recovery and Windows AWG. User order confirmed:
  finish Windows, then Android transports, then stage5 Reticulum; updater/Play not gates.
  [Profile and CI evidence](releases/2026-09-11-windows-tcp-profile.ru.md).

### Earlier Windows engine checkpoint

- Windows TCP engine foundation completed, source ba929a0. Pinned Xray/Go and signed
  Wintun build passed actual Windows CI 34629412460; phase0 passed. Two fresh TUN/VLESS
  runs delivered 12/12 local HTTP responses; forced exit/adapter cleanup passed twice,
  default IPv4/IPv6 routes and DNS preserved. Downloaded binaries match build manifest.
  Preview only: REALITY/external VPN, broker/profile/routes/DNS integration, AWG and
  physical Windows acceptance remain pending. No release/install/server change.
  Next: Windows broker TCP lifecycle and validated protected REALITY profile.
  User network/load tests and Android updates remain deferred.
  [Windows engine evidence](releases/2026-09-11-windows-tcp-engine.ru.md).

### Earlier setup release

- Standalone TCP Setup0.1.0 published separately, source7eee3c3.281 tests and exact
  platform/TCP/AWG/phase0 CI passed. Downloaded archive matches prior VM-tested hash;
  detached setup signature created offline/verified with production anchor and published
  as updates/tcp-setup-0.1.0.json. Trusted verifier/anchor are required before bootstrap.
  No device/server changes. User keeps Android manual APK updates deferred; no Android
  update-check button/Google Play rollout. Next: native Windows AWG/TCP transport work.
  [Setup release/trust evidence](releases/2026-09-11-tcp-setup-release.ru.md).

### Earlier desktop release

- Desktop0.2.9 published from42f9d32 after exact Linux/Windows/Android CI; TCP and
  phase0 passed. Downloaded SHA256SUMS/Linux contents verified, Windows preview reviewed.
  Catalog signed offline, sequence8; signature/new-version/rollback checks passed in
  isolated updater state. Devices/server unchanged, network tests deferred. Next:
  trusted initial TCP Setup delivery, native Windows/Android transports/device acceptance.
  [Release evidence](releases/2026-09-11-release-0.2.9.ru.md).

### Earlier release preparation

- Source checkpoint180d79f pushed to main. All exact-source CI passed: clients
  (Linux/Windows/Android), TCP, AWG, phase0. No release job ran. Downloaded CI setup
  matches previously tested SHA256; downloaded Linux archive six files match git180d79f.
  Versions remain0.2.8 in source; review archive must not replace published0.2.8.
  Draft0.2.9 notes prepared; next version bump/exact-source CI/immutable publication
  and offline catalog signing. Installed versions/server unchanged, network tests deferred.
  [CI and artifacts](releases/2026-09-11-platform-ci.ru.md).

### Previous integration checkpoint

- User deferred further network/load tests and requested moving development forward.
  Functionality demonstrated; ordinary-load stability remains an open known limitation.
  Standalone TCP Setup sources/tests/CI/VM recipes integrated from bootstrap worktree
  into main; existing5 client prompt/recovery edits preserved/reviewed. pytest.ini now
  excludes operator archives from discovery.273 tests and display-backed GTK recovery
  passed; setup builds reproducibly to the previously VM-tested hash, six-file desktop
  compatibility retained. No install/server/network changes, CI/push/release not run.
  Next: source checkpoint/platform CI and trusted setup/new client release preparation.
  [Integration and deferred tests](releases/2026-09-11-setup-integration.ru.md).

### Earlier network evidence (further testing deferred by user)

- Isolated fresh-engine matched checks passed twice: TUN60/60, SOCKS60/60,
  direct60/60 concurrent +80/80 before/after. Installed Xray hash verified in container.
  All60 local TUN handshakes matched, max0.482ms; capture drops0, external socket peak6.
  Short low-load windows13.6/27.5s did not reproduce host failures; background load vs
  namespace/path remains unresolved. Containers removed, host rules unchanged, VPN off.
  Next: bounded isolated concurrency steps with fresh engines and per-request capture.
  [Isolated comparison](releases/2026-09-11-first-laptop-isolated.ru.md).

### Earlier offload comparison

- First-laptop pinned-all offload comparison completed. Final exact A/B/A VPN16/20→18/20→14/20,
  direct20/20 in all five phases. Twelve VPN TCP-connect timeouts; no DNS dependency.
  Offload disabling did not eliminate failures. Xray FD64→89→157 far below limit;
  sockets/queues grew, causal attribution remains open. Ettool TSO restoration also
  toggled mangleid; operator restore now uses two calls and full-feature equality passed.
  VPN off, exact rules cleanup and all feature restoration verified; no test timers.
  Next: isolated matched TUN/SOCKS/pinned direct with fresh engine and request timing.
  [Offload report](releases/2026-09-11-first-laptop-offload.ru.md).

### Earlier paired capture

- First-laptop paired headers completed: VPN35/40, direct39/40 during VPN,
  direct20/20 before/after. Four VPN TCP-connect timeouts and one DNS timeout;
  direct failure also DNS (shared resolver); pinned direct32/32. Zero capture drops.
  78 matched flows with outbound missing suffix retried >=10s, including53 with
  server prefix1327/no payload response; NIC vs external loss remains unproven.
  Exact cleanup passed, VPN off, server unchanged. Next: pinned-all control and bounded
  offload A/B/A with socket snapshots and restoration guard.
  [Paired report](releases/2026-09-11-first-laptop-paired.ru.md).

### Earlier first-laptop baseline

- First-laptop off→on→off now completed: normal-user direct20/20, pkexec→runuser
  direct20/20 before, VPN19/20 with direct20/20, direct20/20 after. Baseline contexts
  identical. One VPN HTTP-response timeout AFTER successful TLS; earlier second-laptop
  TLS timeout cause not established. Full IPv4/IPv6 rules restored, TUN/marker absent,
  VPN off. No code/install/server changes. Next: paired headers with current peer filters.
  [First-laptop result](releases/2026-09-11-first-laptop-resume.ru.md).

### Previous handoff (superseded for first-laptop test status)

- User paused second-laptop diagnosis and requested moving subsequent tests to first laptop.
  Transfer/tests on first have NOT started. Second last checked: TCP inactive; TSO/GSO on/on,
  rollback timers absent. Offload A/B/A completed, but control path failed too; inconclusive.
- TCP bootstrap and signed component installed on Ubuntu24.04.5 amd64, separate client
  provisioned, GUI import/connect/disconnect verified. New TCP identity added on gateway;
  previous TCP/WG/AWG identities preserved. Stable release versions above unchanged.
- Repeated password mechanism reproduced and client fix installed on second: standalone
  TCP monitors without automatic privileged restart; no redundant down for inactive final TCP.
  Main264 tests and GTK recovery passed. Fix is in uncommitted main files, not a published release.
  Repo pilot on first reads changed main on next launch; installed stable0.2.7 remains unchanged.
- Network failures unresolved: new Wi-Fi improved VPN36/40 vs direct40/40; timeout persists
  at10s. Bidirectional capture zero drops,23/116 selected flows show outbound payload gap.
  Offload A/B/A VPN1/20→3/20→1/20; direct0/20→1/20→0/20, so no causal offload conclusion.
- Standalone setup sources remain /tmp/fc-tcp-bootstrap, archived locally;269 tests originally,
  combined worktree273 after client fix. Independent-kernel Debian VM installation passed.
  Packaging integration, remote CI, trusted setup publication and new client release pending.
- Ubuntu appearance/terminal transfer, backups, all tests and next actions are recorded in
  [complete checkpoint](releases/2026-09-11-session-checkpoint.ru.md),
  [network report](releases/2026-09-11-ubuntu-network.ru.md),
  [appearance/rollback](ubuntu-laptop-settings.ru.md).

## Earlier milestones (historical state)

- Manual cancellation of the new TCP updater passed on laptop: genuine pkexec 126,
  GTK cancellation message, busy cleared/selection preserved, no repeat for 18 seconds.
  Component hashes and backup list unchanged; no policy/cache changes. Source unchanged.
  Next: trusted bootstrap distribution for clean Linux machines, VM/hardware acceptance
  and new client release. Stable app/server/published TCP unchanged.
  [Manual updater cancellation](releases/2026-09-11-tcp-updater-cancel.ru.md).

- Root-owned TCP updater and GTK pilot install implemented and installed on laptop.
  Fixed-operation broker verifies its trusted files and signed catalog; GUI confirms,
  handles cancellation and blocks busy/connected installs. Real desktop GTK→pkexec→broker
  signed installation passed; installed files match source/published TCP 0.1.0, TCP inactive.
  260 tests, 24 Xvfb layouts, 6 pilot geometries and recovery passed; screenshot reviewed.
  Host layout timing assertion also fails on previous UI; retained observation.
  Backup directory root:root mode corrected 0775→0755 after safe bootstrap refusal.
  Stable app/server unchanged; next pilot launch exposes button. All remote CI passed
  for 92308a4 (clients/TCP/AWG/phase0);
  manual Cancel now passed; fresh-machine bootstrap distribution and new client release remain.
  [Updater/UI report](releases/2026-09-11-tcp-updater.ru.md).

- TCP component **0.1.0 published and signed**, source/tag 7d1e738, catalog sequence 1
  in commit 53a000c. All main platform/TCP/AWG/phase0 CI and TCP tag release passed.
  Downloaded artifact matches local repack; fresh systemd DNS/HTTPS/reinstall/SIGKILL
  acceptance passed. Public HTTPS fetch as non-root and production-signature root install
  passed, followed by DNS/HTTPS and cleanup; disposable container removed.
  Stable laptop/server unchanged. Next: root-owned broker/bootstrap + explicit UI install,
  then native Windows/Android and VM/hardware gate before broad rollout.
  [Published pilot and evidence](releases/2026-09-11-tcp-release.ru.md).

- Authenticated TCP delivery implemented as an operator CLI: separate Ed25519 domain,
  component sequence/version floors, bounded HTTPS/hash/archive checks and root reverify.
  250 tests passed; ephemeral-key real bundle install/reinstall passed in Debian systemd.
  Initially tested with ephemeral key; production signature/public HTTPS now passed above.
  Remote CI and first TCP publication now completed; trusted broker/bootstrap and UI
  integration remain before broad rollout.
  [Delivery report](releases/2026-09-11-tcp-delivery.ru.md) · [Runbook](tcp-delivery.ru.md).

- Real systemd acceptance passed in a fresh Debian 12 Docker container (shared host kernel).
  Found/fixed missing procps/sysctl dependency: installer now refuses before writes.
  Corrected bundle: fresh install, actual resolved + application DNS, 6 VPN HTTPS checks,
  active-install refusal, stop/reinstall/profile preservation and SIGKILL ExecStopPost cleanup.
  IPv4/IPv6 rules restored, table/TUN/marker absent; both test containers removed.
  230 tests passed; filesystem tamper/rollback suite passed again. No host/server upgrade.
  Next: authenticated component delivery, native Windows/Android and platform CI;
  independent VM/hardware clean-install coverage remains a rollout gate.
  [Systemd evidence](releases/2026-09-11-tcp-systemd.ru.md).

- Separate Linux amd64 TCP component bundle implemented: deterministic archive, checksum
  preflight, active-service refusal, private backups, per-file atomic replacement and
  rollback on failure; existing profiles preserved and service never auto-started.
  229 Python tests passed; isolated filesystem install/tamper/upgrade/reload rollback passed.
  Xray matches cached pinned-revision image; repeated archive SHA256 identical.
  Initial filesystem test used stubs; real systemd container acceptance is now recorded above.
  CI artifact steps added but remote CI/signing/release not run; host install unchanged.
  [Bundle report](releases/2026-09-11-tcp-bundle.ru.md) · [Install runbook](linux-tcp-install.ru.md).

- TCP source integration into main completed after targeted review: installer refuses
  active/pending TCP state before writes; WG health prefers paired AWG endpoint when
  TCP differs. Full main suite 226 passed, GTK regression/kernel namespace checks passed,
  six-file updater archive compatibility verified. Review fix ca2a63a retained in pilot branch.
  Stable installed app/server unchanged; repository-based AWG pilot launcher now uses TCP
  backend on next launch. System helper dependencies were not reinstalled automatically.
  Next: reproducible clean-Linux component packaging/install, native platform integration,
  then fresh platform CI/new signed release. No push/remote CI/release yet.
  [Integration review and rollout limits](releases/2026-09-11-tcp-integration.ru.md).

- Manual system authorization cancellation passed: real TCP-helper pkexec returned 126,
  actual AuthorizationError reached recovery completion, policy stopped; no repeat pkexec
  for 18 s and no TUN. Watchdog/controller cleanup passed, no UDP fault or polkit changes.
  Recovery state was staged for this cancellation case; earlier full GTK network recovery
  supplies separate end-to-end coverage. Functional Linux pilot checklist now exercised.
  Next: review/integrate experimental diff, then current tests/CI and release preparation.
  Initial unlocalized backend AssertionError remains an open observation; not a reliability guarantee.
  [Manual cancellation evidence](releases/2026-09-11-polkit-cancel.ru.md).

- Real GTK/production LinuxTCP/pkexec recovery passed: established AWG → TCP in 59.88 s;
  connected/restored UI, selected profile preserved, actual Disconnect and close-after-
  disconnect passed. Root controller applied only endpoint UDP fault and verified cleanup.
  GTK recovery regression also passed, including injected AuthorizationError.
  Close-while-connected real dialog also passed: cancel preserves monitoring, confirm
  stops monitoring and leaves VPN as warned; controller then disconnected/cleaned it.
  Real polkit Cancel now passed in a separate test; no policy changes
  or temporary-authorization revocation were used. Stable launcher/releases unchanged.
  [GTK live evidence and acceptance limits](releases/2026-09-11-tcp-gtk.ru.md).

- Established AWG → TCP backend/policy recovery exercised on the laptop: one initial
  unlocalized AssertionError, then two successive passes at 45.32 s and 45.57 s after
  two failed health cycles. Real endpoint UDP blocks counted 1047/1154 packets.
  Unprivileged TCP health, resolved query, disconnect policy stop and cleanup passed.
  All three attempts cleaned up; no tunnels/test firewall left. No product code change.
  First failure remains an open observation; not a GTK/polkit end-to-end acceptance.
  Next: real experimental Linux UI/recovery/authorization-cancel acceptance before release.
  [Recovery evidence and limits](releases/2026-09-11-awg-tcp-recovery.ru.md).

- Corrected TCP helper installed and short laptop smoke passed: 3 bound HTTPS health
  checks, resolved query, gateway bypass/public TUN route, 3 local routes preserved.
  Cleanup restored complete IPv4/IPv6 policy-rule baseline; TUN/marker absent.
  Backup: /var/backups/family-connect/tcp-routing-1789119289/helper.
  New helper remains installed; test tunnel stopped. Main launcher/stable releases unchanged.
  Bounded backend/policy recovery now has two passes; see latest report above.
  [Installed-helper report](releases/2026-09-11-tcp-host-smoke.ru.md).

- New Wi-Fi baseline and TCP retest completed: gateway max 53.9 ms (was 496),
  Wi-Fi retries +7 (was +433); all baseline targets/HTTPS 30/30. Matched TCP test
  passed 120/120: direct/TUN/SOCKS HTTPS and direct/TUN DNS each 24/24, cleanup passed.
  Code/timeouts unchanged. Bounded isolated acceptance passed; not a long-run guarantee.
  Corrected helper installation/short smoke now passed; AWG → TCP recovery remains.
  User has completed network change; no further switch is pending.
  [Network-change comparison](releases/2026-09-11-network-change.ru.md).

- Current roadmap: **stage 4, client packaging/platform acceptance**. WG works;
  AWG/recovery passed in Linux pilot, not yet a cross-platform stable rollout.
  [Development roadmap](ROADMAP.ru.md).
- Local-link comparison completed: Wi-Fi gateway 30/30, median 31.35 ms, max 496 ms;
  VPS 26/30, control 28/30, direct HTTPS 30/30 (up to 2.608 s). Correlated gateway,
  control and HTTPS delays; Wi-Fi retries +433 including background traffic.
  Local network contributes jitter; this does not explain every prior TLS failure.
  Superseded by successful retest after user changed Wi-Fi; see latest result above.
  No installed code changed.
  [Local-link evidence](releases/2026-09-11-local-link.ru.md).

- Paired TCP-header diagnosis completed (experiment `2674d20`): 72/72 handshakes matched across client/server.
  In the failing round client SYN→SYN-ACK took 0.788–1.315 s, while server response
  took 9–73 microseconds (max across all flows 0.846 ms); two SYN retries were observed
  at both ends. Delay is outside server SYN processing; loss location is not proven.
  Full series: direct/TUN HTTPS 24/24, SOCKS 23/24, both DNS 24/24, server HTTPS 30/30.
  Post-test host routes use Wi-Fi/main. Next: compare local gateway/VPS latency and
  wireless counters before any host rollout. Capture cleanup passed; no deployment.
  [Paired capture report](releases/2026-09-11-tcp-packets.ru.md).

- Matched TCP diagnostics completed (experiment `d776b41`): two isolated 24-round series with identical HTTPS
  endpoint/timeouts. TUN 48/48, SOCKS 47/48, direct 47/48; tunnel UDP DNS 46/48,
  direct UDP DNS 45/48. SOCKS failure was TLS setup timeout; direct failure occurred
  after TLS while waiting for HTTP data. Gateway TCP snapshots show SYN-SENT/retrans,
  without per-request socket attribution. Root cause/censorship not established.
  Both cleanup checks passed. No host install, server mutation or release.
  Paired TCP-header comparison is now complete; see latest report above.
  [Matched diagnosis](releases/2026-09-11-tcp-matched.ru.md).

- TCP routing correction implemented in experimental commit `6d7f569`: preserve more-specific
  main routes; explicit gateway /32 bypass plus prohibit-on-missing-route; exact cleanup,
  collision checks, legacy marker support and retry after cleanup failure.
  Real-kernel network-none container checks passed; 222 Python tests passed.
  Not installed on the laptop; no host VPN test or server change in this stage.
  Isolated live traffic: first TUN/SOCKS 24/24 each, UDP DNS 23/24; expanded comparison
  TUN 24/24, SOCKS 22/24, tunnel UDP DNS 23/24, TCP DNS 22/24, direct UDP DNS 22/24.
  Cleanup passed. Direct DNS also timed out; all prior instability is not resolved.
  Matched comparison completed below the routing milestone; see latest diagnosis above.
  [Routing correction](releases/2026-09-11-tcp-routing.ru.md).

- TCP diagnosis update: direct server HTTPS 36/36; long SOCKS-only comparison 216/216
  checks passed, but long full-TUN comparison degraded (including independent SOCKS).
  Local HTTP stayed 36/36. Packet capture confirms gateway-directed RST on TUN;
  no gateway SYN on TUN was found. Code review found missing preservation of more-specific
  main-table routes before TUN lookup. This is a concrete routing defect; it does not yet
  prove the cause of every timeout. No correction installed or release published.
  TCP service/tunnel/test rules are verified off/removed; main WG/AWG code unchanged.
  [Diagnosis and evidence](releases/2026-09-11-tcp-diagnosis.ru.md).

- TCP experiment: VLESS + REALITY deployed separately on TCP/443; Xray 26.3.27.
  Linux TUN/helper installed; isolated HTTPS/DNS and unauthorized-client rejection passed.
  One real blocked-WG/AWG → TCP run passed in 16.81 seconds. Repeated requests still
  time out; increasing probe timeouts did not resolve this. Cause remains unknown.
  222 Python tests (78 desktop), GTK layout/recovery checks passed locally; no CI/release.
  Source checkpoint `fa3c71e` is preserved separately in local branch `pilot/tcp-reality-2026-09-11`;
  main WG/AWG launcher and stable app remain on previous code. TCP service is inactive
  on the laptop; interface, policy rules and test firewall tables verified removed.
  Server TCP container remains deployed. Resume diagnosis before integrating/releasing TCP.
  [Checkpoint and next diagnostic step](releases/2026-09-11-tcp.ru.md).

- User priority: connection resilience. AWG 2.0 pilot deployed separately on UDP/51821;
  existing WG/three peers preserved. Linux root helper installed and real host AWG
  handshake/HTTPS verified. Real blocked-WG → AWG fallback test passed, then cleaned up.
  Client implementation is an unreleased working-tree pilot; installed stable 0.2.7
  and published 0.2.8 catalog remain unchanged. Separate AWG pilot launcher available.
  AWG milestone: 189 Python tests passed (45 desktop). Upstream engine tests, isolated AWG data
  test, 24 GTK layouts and six additional pilot-label layouts passed.
  Established-session monitoring/recovery now implemented in the open Linux pilot:
  15-second checks, two failed cycles, three bounded attempts with 15/30/60-second backoff.
  Explicit disconnect/selection/close/auth cancellation stop recovery. Two independent
  bound HTTPS probes; 199 Python tests and GTK recovery/layout checks passed.
  Established WG endpoint block recovered through AWG in 44.05 seconds on the laptop.
  Updated root helper installed; no new stable release or server change in this stage.
  Native Windows/Android AWG, stable TCP integration and Reticulum delivery remain pending.
  Same server/IP and UDP limitation. [Recovery report](releases/2026-09-10-recovery.ru.md).
  [AWG rollout report](releases/2026-09-10-awg.ru.md) · [evidence](awg-resilience-result.json).

- Windows now follows the Linux 0.2.7 composition: compact branding, rounded status card,
  single-column buttons, smaller typography, content-sized startup window, themed
  confirmation/device-code dialogs and dark main title bar on supported Windows.
  Windows-specific activation and broker behavior preserved. Initial connection status
  no longer becomes Working during unrelated actions.
- Windows runtime checks: 96 layouts (RU/EN, four states, three sizes, 100–250%),
  nested card labels, polling/stale replies and confirmation cancellation; broker,
  installed UI and driver checks passed. CI-generated preview saved below.
- 0.2.8 artifacts downloaded and SHA256SUMS verified before offline catalog signing.
  Catalog sequence 7; signature verified from published commit 3171fed. Main raw URL
  propagation now verified with the installed updater: old version detects 0.2.8 and
  0.2.8 detects no newer version. Earlier cached 0.2.7 response is resolved.
  No personal Windows machine was accessed; user must run the installer or in-app update.

- Android test APK from successful CI shared with user (debug build, profile import).
  Existing local `state-v2/pilot-clients/fc-ru-android.conf` verified against active and
  persistent gateway public key/addresses; mode 0600, ignored by Git. Phone import,
  handshake and external-IP test remain pending. No Android key rotation or server change.
- Windows device code after reinstall matches the existing peer at 10.77.0.4. Fresh
  signed activation issued locally under `state-client-build/activation/`, expires for
  import 2026-09-11 19:53 UTC. Import on Windows and actual connection test remain pending.
  Existing three peers preserved; no gateway mutation/restart was needed.

- Linux frontend now uses GTK 4/libadwaita. Compact header, rounded connection card,
  native selector/dialogs, one column of actions and content-sized height. Initial data
  is applied together; unchanged polling does not change widget properties.
- Installed from checksum-verified GitHub archive using the existing 0.2.6 updater;
  new GTK startup smoke passed. Current: `~/.local/share/family-connect/current`;
  `~/.local/share/family-connect/previous` retains 0.2.6. Launcher icon/app ID refreshed.
- Real laptop GTK 4.22/libadwaita 1.9 on native Wayland: 390×548 logical pixels.
  Eight-second read-only probe: two initial state renders, no periodic property updates;
  after two seconds warm-up, max/p95 timer interval 16.2 ms at a 16 ms target,
  0.154 CPU seconds. Earlier Tk sample had a 1.4-second gap outside Python handlers.
  User confirmed Linux 0.2.7 appearance and behavior are good.
- Checks: 27 desktop Python tests, 24 GTK layouts (100–250%), coherent initial state,
  unchanged/stale polling, action independence and confirmation cancellation. GTK 4.8 /
  libadwaita 1.2 compatibility verified locally. Windows CI passed broker/UI/layout
  checks; all client jobs and phase0 passed.
- Linux prerequisites: Python GI, GTK >=4.8, libadwaita >=1.2, cryptography and
  NetworkManager. Ubuntu/Debian packages: `python3-gi gir1.2-gtk-4.0 gir1.2-adw-1
  python3-cryptography`. Already present on this laptop; no system packages changed.
  Other hosts must install prerequisites before updating; failed smoke retains old app.
- Catalog `updates/pilot.json`: sequence 7, version 0.2.8, 90-day validity. HTTPS
  downloads, Ed25519 verification, user-confirmed installation. Reticulum delivery
  remains planned. Private signing key stays local under
  `state-client-build/update-signing/ed25519.key` and is never committed.
- Intermediate 0.2.4 release remains immutable without a signed catalog; later versions
  supersede it. Do not overwrite published binaries/tags.
- Server `185.251.89.19:/opt/apps/family_connect`: product API schema 3, localhost
  `127.0.0.1:18082`, gateway/worker/timer deployed in 0.2.1, three legacy peers preserved.
  Backup `/opt/backups/family-connect/20260910-110930`; rollback gateway image
  `family-connect-wireguard:rollback-20260910-110930`. No server changes for this release.
- Live product smoke passed on 2026-09-10: HTTP enrollment/replay rejection, staging,
  periodic worker install/persistence, revision 1 publish/fetch and local signature/decryption
  verification, revoke and rejection of an outstanding fetch proof, periodic worker removal.
  All three legacy peers and allowed IPs unchanged. Test device/entitlement revoked;
  audit and address reservation retained. No real client handshake/runtime apply tested.
  See [live report](live-product-smoke.ru.md) and [result](live-product-smoke-result.json).
- Pending: runtime provisioning/ACK and public HTTPS ingress, Reticulum update delivery,
  native invitation/storage flows; physical Windows/Android connection checks.

[Release](https://github.com/Joker20380/family_connect/releases/tag/v0.2.8)
· [Client CI](https://github.com/Joker20380/family_connect/actions/runs/34522112485)
· [Phase0 CI](https://github.com/Joker20380/family_connect/actions/runs/34522112544)
· [Release report](releases/0.2.8.ru.md) · [Plan](PLAN.md)

Temporary icon: `clients/assets/dodecahedron.svg`; regenerate PNG/ICO/embedded icon
with `python scripts/generate_app_icon.py` (Pillow). Final icon design deferred.
