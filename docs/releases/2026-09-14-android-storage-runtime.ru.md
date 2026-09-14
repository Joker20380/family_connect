# Android CI и защищённое состояние — 2026-09-14

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


## Проверенный исходный checkpoint

Рабочее дерево при входе чистое, HEAD a342d4b; origin/main указан пользователем.
GitHub API подтвердил результаты:

- [Client builds34833797626](https://github.com/Joker20380/family_connect/actions/runs/34833797626): Linux103942924173, Windows103942924357, Android103942924443 success; release skipped.
- [Android diagnostic34833797792](https://github.com/Joker20380/family_connect/actions/runs/34833797792): Android103942924198 success.
- [phase034833797631](https://github.com/Joker20380/family_connect/actions/runs/34833797631): failover103942923625 и tests103942923894 success.

Ошибки предыдущего checkpoint исправлены. API releases/latest вернул404,
список releases подтвердил desktop v0.2.9 (2026-09-11T15:46:52Z), TCP0.1.0 и
TCP Setup0.1.0. CI success не означает установку или deployment.
Проверенный a342d4b имел0.1.2-beta03/code3. После разрешения установки подготовлена
новая версия0.1.3-beta04/code4; опубликованные APK beta03 не заменяются.
Storage checkpoint2ce9a1b отправлен в main; следом version bump для нового CI APK.

## Новая проверка

ControlStorageRuntimeTest запускается только на disposable emulator с явным
fc_disposable=true, без существующих профилей/managed state. Генерирует тестовую
identity прямо в Android и проверяет неэкспортируемость wrapping keys, durable
подписанный REJECTED ACK, отказ повторной identity/journal initialization.
После незавершённой AtomicFile.startWrite вызывается am force-stop; отдельный
instrumentation process загружает те же identity/journal/ACK, проверяет удаление
незавершённого .new, clock regression, сохранение ACK при offline send, flush,
отказ повреждённого authenticated ciphertext без скрытого сброса состояния.
Runner требует разные process IDs и успешный JUnit результат обеих фаз.
CI gate требует основной JUnit case и отдельный JSON receipt; missing/skipped
или отсутствие доказательства нового процесса запрещают success.

Проверки до remote CI: JDK17/Android35 instrumentation compilation passed с
cached dependencies; Python syntax passed; CI gate принимает корректный receipt,
отвергает missing receipt, same-process receipt и skipped storage case.
Новый emulator CI ожидается. Это не proof полного VPN apply/rollback, регистрации
через HTTPS или RNS ACK delivery: sender в storage тесте намеренно локальный.
Полные apply/traffic/recovery остаются отдельными обязательными проверками.

## Устройство и следующий шаг

Пользователь разрешил тестовый телефон и установку новой сборки. USB обнаруживает
Xiaomi Mi/Redmi MTP, adb devices пока пуст; запрошено включение USB debugging и
подтверждение ключа компьютера. Никаких данных телефона не удаляли, APK не ставили.
После ADB: проверить установленную версию и signing certificate без вывода ключей;
подготовить проверенную совместимую тестовую сборку, сохранить identity/profile;
регистрация, публикация offline-signed envelope под Android version/key в ControlRelay,
RNS receive/apply, реальный gateway egress/DNS/HTTPS, ACK, relay outage/reconnect,
process death с pending и восстановление. Затем Windows Stage5 и общий план VPN;
Django/платежи после VPN acceptance, messenger/iPhone отложены.

## Rollout и rollback

Изменения затрагивают androidTest/CI и увеличение Android versionCode/versionName. Deployment/установка/
каталог/подписи/server state не изменены. Rollback — revert нового тестового
checkpoint; сохранять production device data, identity, journal и outbox. Disposable
CI удаляет только созданные им managed aliases/files после проверки. Нельзя запускать
storage runner на пользовательском телефоне или убирать его emulator/pre-existing-state guards.

## Первый CI нового теста

Source babe651, [Clients34836392940](https://github.com/Joker20380/family_connect/actions/runs/34836392940):
Windows/Linux success, Android APK/unit/lint и8 instrumentation methods passed.
Дополнительный storage runner failed: connectedDebugAndroidTest удалил test APK,
am instrument вернул Unable to find instrumentation info. Исправлено установкой
уже собранных target/test APK перед prepare; между prepare и recover переустановки
нет, только force-stop. Это runner fix, не ослабление storage acceptance.
Artifact10344867835,121729505 bytes, SHA256
b08ef967a70d46c5f5b93b5013d1279981ca34312fff689aca4b59284be419d1 проверен.
APK сохранён для диагностики; выпуск/установка по failed CI не выполнялись.
Phase034836392974 tests/failover success. Повторный CI ожидается.

ADB увидел Redmi Note9 Pro/joyeuse, Android12/arm64-v8a, установленный Family Connect
0.1.0/code1/debuggable от10.09.2026. Помог ADB_LIBUSB=1, но bulk USB передача
по-прежнему обрывается; APK для сравнения сертификата пока не получен.
Временно включён tcpip5555, проверяется192.168.129.42:5555; после приёмки вернуть USB.
Профили/app data не читались и не удалялись, APK не установлен.

## Сохранение прежнего приложения

Wi-Fi ADB192.168.129.42:5555 позволил сохранить исходный публичный APK. Его debug
certificate SHA256668409f4b19253908f66a6bcdaf0da77a625e589fece38ccebb59e0c89722e08
не совпадает с локальным debug c2c3da545f0c1171562339934fae275f1cf89a224e0493a924dd73a990e8bca6
или beta67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a.
Для обновления старого CI APK нужный private signing key отсутствует. Uninstall
не выполнялся. Новая debug beta04 получает applicationId com.familyconnect.app.pilot
и label Family Connect Pilot; release ID остаётся com.familyconnect.app. CI выполняет
всю приёмку на фактическом pilot ID. Это отдельная регистрация/identity; migration
старого профиля не заявляется. Следующие pilot APK подписывать одним постоянным
beta key, code увеличивать; не подменять опубликованные версии.

## Принятый CI и установка beta04

Source972c81c, [Clients34838248178](https://github.com/Joker20380/family_connect/actions/runs/34838248178):
Linux103957035071, Android103957035298, Windows103957035500 success; release skipped.
[phase034838248234](https://github.com/Joker20380/family_connect/actions/runs/34838248234):
tests103956952462/failover103956952866 success.8 instrumentation cases и отдельные
prepare PID5620/recover PID5655 passed; packaged RNS internal crypto/corpus passed.
Artifact10345416969,120478185 bytes, SHA256
2e04f9ec8e4fd3cddbd06d9b465d93cd30a6281b4080cea386f3ec422cec96c1.
Проверены все4 native ABI, Python/RNS, packaged bootstrap/anchor/licenses и отсутствие
fixtures. ARM64 packaging сохранил байты retained payload; zipalign16KB/signature passed.
Установлен state-client-build/android-pilots/beta04/FamilyConnect-Android-0.1.3-beta04-arm64.apk,
77686846 bytes, SHA256 b6df64f0f4d0d16602900221bd605e7b3e07779a36633b9e7eb6c4930eae9365.
Сертификат постоянного offline beta key67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a.
Это debug technical pilot, не публичный release. Исходный0.1.0 остаётся установлен.

## Live enrollment, configuration1 и незавершённая приёмка

На реальном Redmi Note9 Pro/Android12 пользовательский UI зарегистрировал новую
native identity через https://185.251.89.19:8443; proof/key binding подтверждён.
Device reference dc899995df4dafd51177ca28ab1d4382. Private invitation/binding хранятся
только state-enroll/android-stage5-pilot (0700, files0600). До создания приглашения
в private product DB directory сохранена android-stage5-before-20260914.db;
не восстанавливать весь DB поверх последующих регистраций.

В Amsterdam fcams добавлен только отдельный peer10.79.0.5/32,fd79:92::5/128;
прежние3 peers сохранены, interface не перезапускался. Offline signed schema2
android-live-1/revision1, expiry2026-09-14 13:53:02UTC; envelope SHA256
055cf9423aebc5c120cd489f533a98a2403de48899818fc870810f14386fd2e0.
Опубликован в существующем ControlRelay без restart. На relay проверены device signatures
RECEIVED/APPLIED timestamp1789386931 и COMMITTED1789386932, sequence1/errorNONE.
Gateway зарегистрировал handshake и рост двусторонних счётчиков; commit требует
DNS и HTTPS через конкретный VPN Network. Отдельный внешний IP ещё проверяется.

Несколько reconnect завершились IOException в ControlTransaction:96 (Resume health
failed); один последующий reconnect успешен. Диагностика debug JDWP выводит только
type/stack locations и boolean/null готовности Network, без exception values/keys/profiles.
Причина нестабильности ещё не доказана; тайминг публикации VPN Network проверяется.
Полная приёмка восстановления, crash pending rollback, AWG/TCP и blocked-WG открыта.
Наблюдение пользователя о блокировке WG в российских сетях делает AWG/TCP обязательными;
WG baseline не является приёмкой России.

UI обновляет TextView каждые500ms: uiautomator idle dump не завершается. MIUI
input tap запрещён; разрешённые AccessibilityNodeInfo actions работают через временный
shell UiAutomation helper. Helper может вернуть137 после успешного action; не считать
такой exit доказательством отсутствия нажатия. Это открытая проблема автоматизации/UI.

Возврат: остановить только pilot, сохранить его identity/journal и исходное приложение.
Для нового peer есть exact-stanza cleanup: на186.246.45.246 выполнить
python3 /opt/apps/family_connect/android-stage5-peer.py cleanup; откажет при изменённой
stanza. Private backup/receipt в /opt/apps/family_connect/android-stage5-pilot.
Timer family-connect-android-pilot-expiry удаляет только этот peer через130min;
проверить его результат. Не переиздавать revision1 с иными bytes/reset journal.
После испытаний убрать временный /data/local/tmp/fc-ui-dump.jar и JDWP port8700,
вернуть adb usb, закрыв временный Wi-Fi listener5555. Это пока незавершённые действия.

## Live WG recovery и AWG2

WG external IP через bound HTTPS:186.246.45.246/NL. Force-stop только pilot → новый
process → явный Reticulum connect восстановил VPN/DNS без новой revision/ACK transaction.
Это один принятый restart, не объяснение предыдущих health refusals.
AWG2 config android-live-2/revision2 получена автоматически в работающей сессии;
previous hash указывает на config1. Envelope SHA256
3855cdce4297d05c357b5031a0870b42adc9254899f0b5687bdde9197dc414f4,
expiry epoch1789391100. RECEIVED/APPLIED1789387526, COMMITTED1789387527/errorNONE.
Внешний IP185.251.89.19 (trace locRU) подтверждён через AWG VPN Network.
UI ошибочно подписывал весь AWG slot как3.1; исходник исправлен на AmneziaWG,
установленный beta04 пока содержит старую подпись. Managed schema2 здесь именно2.0.

Добавлен только AWG peer10.78.0.3/32,fd78:92::3/128 на185.251.89.19;
исходный peer сохранён. Backup /opt/apps/family_connect/android-stage5-awg-pilot/awg-before.conf,
exact-stanza cleanup python3 /opt/apps/family_connect/android-stage5-awg-peer.py cleanup;
таймер family-connect-android-awg-expiry удаляет только этот peer через70min.

Для health-failure rollback опубликован android-live-3/revision3 (AWG endpoint
185.251.89.19:51999), previous hash config2; серверный firewall не меняется.
Envelope SHA256 bee4bee1523557981066d7834de6d1248315a90b82c1e8771e25549ff62f5e18.
Результат rollback пока ожидается; не перепубликовывать revision3 и не сбрасывать floor.

## Health rollback и crash pending rollback приняты в live pilot

Revision3: RECEIVED1789387649, APPLIED1789387650, ROLLED_BACK/HEALTH1789387655;
после отката bound HTTPS показал185.251.89.19/RU через сохранённый AWG2.
Для revision4 тот же недоступный endpoint, previous hash остаётся config2:
SHA256643f32bdbfff2806c20bd0d76e6c6cc63647e0a2432ddcd8a7a770a6592f5a95.
В debug APK JDWP breakpoint в ControlApplication.healthy остановил процесс после
persist APPLIED_PENDING (до health/COMMITTED). Подтверждён CRASH_POINT_REACHED;
am force-stop только com.familyconnect.app.pilot, затем новый запуск и явный RNS.
Сохранённые RECEIVED/APPLIED1789387778 доставлены из outbox после restart;
ROLLED_BACK/RECOVERY1789387817 подписан тем же устройством. Повторный bound HTTPS
185.251.89.19/RU подтвердил реальный трафик через восстановленный AWG2.
Ни одна fault revision не получила COMMITTED, replay floor не сбрасывался.

Телефон находится в Европе (уточнено пользователем). Эти результаты подтверждают
pipeline/runtime, но не доступность WG/AWG/TCP из России. WG блокируется в российских
сетях пользователя; для целевой сети нужны независимые AWG/TCP acceptance.

## Изолированный TCP pilot — подготовлен

На185.251.89.19 создан только family-connect-android-tcp-pilot, TCP8444→container8443;
прежний family-connect-tcp-gateway-1/TCP443 не перезапускался. Закреплённый image
sha256:865c9e3311707e87476611c4fd65dc840ef5b4addf7bac5822e08245e59a5453,
Xray26.3.27/d2758a0. Новый отдельный UUID, private config в
/opt/apps/family_connect/android-stage5-tcp-pilot; server REALITY key остаётся на
том же gateway, не загружался локально/вGit. Серверная конфигурация uid65532:65532,
0600, каталог0700; readonly container, cap-dropALL,128MiB/64pids, tmpfs/tmp.
Первая config validation отказала из-за root-owned0600 нового файла; после назначения
ожидаемого uid65532 explicit xray run -test passed. Существующие config/users не менялись.
Таймер family-connect-android-tcp-expiry останавливает только pilot через70min.
Rollback: docker stop family-connect-android-tcp-pilot, затем убрать только этот
временный container; private files сохранить до сверки результата. Firewall не менялся.

Подписан/опубликован android-live-5/revision5, previous hashconfig2; TCP credential
доставляется только в encrypted envelope. SHA256
828e5e1c493b76fbfe36860b7e9ef38787276773bcf1edd5ef9cb1e02a838399.
TCP apply/traffic/ACK пока ожидаются. Это отдельный порт8444, не приёмка TCP443 из России.

## TCP Internet/restart и короткая lease

Revision5 RECEIVED/APPLIED1789388063, COMMITTED1789388064/errorNONE.
Bound HTTPS external IP185.251.89.19/RU подтверждён на TCP; после force-stop и явного
RNS connect TCP восстановился, повторный external IP тот же. Новая регистрация не нужна.
После этого подписана TCP revision6, previous hashconfig5, срок120s:
expiry2026-09-14 12:19:37UTC, envelope SHA256
3ab6c2fa31dc54ac4606cb21d934833b5be4faae76328f212de848dd6a4e3986.
Проверка expiry stop/refusal и уборка временных ресурсов ещё выполняются.

Checkpoint a857e4f отправлен в main. Clients34841760104: Windows103968142314 и
Linux103968142639 success; Android103968142610 пока выполняет emulator lifecycle.
Phase034841760207 tests103968142203/failover103968141872 success.
Новый APK этого checkpoint не подписывался/не устанавливался; телефон остаётся
на accepted972c81c beta04 с исходным SHA. В исправлении подписи AWG native engine не менялся.

## Обнаруженный transient health refusal и beta05 source

Revision6 НЕ COMMITTED: RECEIVED1789388265, APPLIED1789388266,
ROLLED_BACK/HEALTH1789388267. Поэтому автоматическая остановка по её expiry не
проверена. Позднее relay получил REJECTED/LEASE1789388390 для её hash: отказ
просроченного envelope подтверждён. Следующая revision7, previous hashconfig5,
SHA256ed3b4290ee78f0b8fbb80dafbcd0c56065b1d4380276e7bc2d557354a50a591c,
RECEIVED1789388455, APPLIED1789388462, COMMITTED1789388468. Это последний committed
hash; следующий выпуск конфигурации должен иметь revision>7 и ссылаться именно на него.
Non-suspending JDWP trace на этом успешном повторе показал Network present/DNS true;
точная причина предыдущего краткого отказа не доказана, влияние самого debugger
на тайминг не исключено. Диагностический debugger отключён.

В исходниках0.1.4-beta05/code5 добавлен ControlHealthRetry: повтор только bound
DNS/HTTPS до прежнего общего15s deadline, проверка отмены и late-success refusal.
Произвольного default-network fallback нет. Цель — убрать преждевременный отказ при
асинхронной готовности Android Network или кратком сбое пробы; fixed deadline сохранён.
MainActivity обновляет state/health/toggle/error TextView только при изменённом тексте,
чтобы idle UI не порождал бесконечные accessibility text-change events.
Local JDK17/aapt2/Android35 app compilation passed;104 control tests passed,
включая6 readiness/deadline/cancellation/interruption cases. Один cached AndroidX
annotation warning; native emulator/real phone beta05 ещё не проверены.
Самостоятельный aapt2 harness требовал package namespace, добавленный только в /tmp
копию manifest; production manifest/Gradle namespace не менялись.

CI a857e4f завершён: Clients34841760104 Linux/Windows/Android success, release skipped;
phase034841760207 tests/failover success. APK этого checkpoint не устанавливался.
Новый beta05 CI/ARM64 packaging/offline signature/install и lease test впереди.

[Sanitized live receipt](../android-stage5-live-result.json): подписи ACK проверены
перед выгрузкой; профили, tokens, private keys и TCP credentials отсутствуют.

## Beta05 первый CI: checksum service outage и скрытый pipeline failure

Source5356ab4, Clients34843155641 Android103972622858 остановлен APK gate.
Native build log: go mod tidy не смог проверить github.com/xtls/reality через
sum.golang.org/tile/8/0/x201/224 (HTTP2 INTERNAL_ERROR). Pipe `build.py | tee` без
explicit bash pipefail ошибочно вернул0; Gradle продолжил сборку. APK имеет
размер55661222 bytes; в нём нет ни assets/awg-build.json, ни четырёх libfc-awg.so.
Последующий verify-apk правильно отказал. Artifact10347131108,32560862 bytes,
SHA2560321d63b1b2cc422e39128ae8313c6e7416ae6fd17552d8f3478b3437712eb0a
скачан только для диагностики в /tmp/fc-android-beta05/failed-5356ab4; подпись/
установка не выполнялись. Это не успешный native CI и не проблема Android health кода.

Оба workflows теперь задают explicit shell:bash для native pipeline (pipefail).
Go mod tidy имеет не более3 попыток, паузы2/4s, исходные checksum verification и
GOTOOLCHAIN сохранены. Последний отказ по-прежнему завершает сборку ошибкой.
Локально проверены propagation `false | tee`, success-after-two-failures и terminal
failure-after-three; Python syntax passed. Новый source CI ещё предстоит.

Принятая revision7 истекла12:30:03UTC; после этого UI показал VPN off, dumpsys activity
services для pilot — nothing. Автоматическое expiry отключение принято на beta04.
Запрошен повторный RNS connect для проверки expired refusal; результат ещё ожидается.

Explicit shell:bash и добавление pipefail подтверждены
[официальным workflow syntax reference](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#jobsjob_idstepsshell).
Повтор expired revision7 дал подписанный REJECTED/LEASE1789389095 и1789389155;
новый TUN не поднялся. UI остался в ожидании relay («Подключение…») с текстом отказа;
оператор нажал «Отключить». Отдельный статус ожидания конфигурации остаётся UI улучшением.

## Частичная уборка во время beta05 CI

Временный WG peer10.79.0.5/fd79:92::5 в Amsterdam удалён exact-stanza cleanup;
временный AWG peer10.78.0.3/fd78:92::3 на185.251.89.19 удалён таким же scoped cleanup.
Оба соответствующих expiry timers остановлены до ручной уборки. Исходные peers
не удалялись, private backups/receipts сохранены. Для beta05 остаётся отдельный
TCP8444 container с таймером и Wi-Fi ADB; их уборка ещё впереди.

## Исправленный CI8b6d51b принят

[Clients34843986160](https://github.com/Joker20380/family_connect/actions/runs/34843986160):
Android103975351009, Windows103975350690, Linux103975351163 success; release skipped.
[Android diagnostic34843986164](https://github.com/Joker20380/family_connect/actions/runs/34843986164):
103975350698 success. [phase034843986155](https://github.com/Joker20380/family_connect/actions/runs/34843986155):
failover103975350079/tests103975350461 success. CI acceptance wrapper проверил exact
full SHA8b6d51b87769248fb0f1519c2916925b8f5507bd и conclusions всех трёх workflows.
Artifact10347930896,121754674 bytes, expected SHA256
89b1c9c99f466e8b0a182c221c2284d971bda30a2f47b1c419f368e4b3762578;
скачивание/локальная проверка/подпись/установка beta05 ещё выполняются.

## Проверенный ARM64 beta05

Artifact digest подтверждён;132 app unit cases и8 instrumentation cases без
failures/errors/skips. Storage restart prepare5836→recover5870 passed. Native hashes,
Python/RNS/bootstrap/anchor/licenses/fixture gates passed. ARM64 selection сохранил
retained payload; zipalign16KB и offline подпись постоянным beta key verified.
APK0.1.4-beta05/code5,77686846 bytes, SHA256
e83c0841dfa3719e50bef3509fdb436ce7f2fb17c8479c556fa13d80d974d951.
Public receipt и APK: state-client-build/android-pilots/beta05/. Source8b6d51b,
certificate SHA25667a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a.
Команда adb install -r выполняется; фактическая версия/runtime ещё проверяются.

## Beta05 установлена; revision8 принята

adb install -r завершился Success; dumpsys package подтвердил pilot0.1.4-beta05/code5
и неизменённое исходное com.familyconnect.app0.1.0/code1. Регистрация не повторялась.
Новая revision8 требует min_client_version0.1.4, previous hashconfig7, expiry epoch
1789390735. SHA256fdc106fed72d7ce6a3199fe3c2cfd96436abff1544122829142c74ab21348bd9.
RECEIVED1789390467, APPLIED1789390468, COMMITTED1789390469/errorNONE подписаны прежней
identity. Bound HTTPS external IP185.251.89.19/RU подтверждён. Повторные reconnect и
force-stop recovery beta05 пока выполняются. Исходный native APK retained payload
проверен; установка по failed5356ab4 не выполнялась.

## Итог beta05 и выполненная уборка

Три последовательных цикла beta05 прошли без debugger: disconnect/reconnect45.34s,
disconnect/reconnect40.90s, force-stop/new-process/reconnect43.54s. В каждом bound HTTPS
IP185.251.89.19. Эти timings включают ADB/UI/RNS и не являются временем health probe.
Relay сохранил одну revision8 apply transaction с прежними тремя ACK/timestamps.
Standard uiautomator dump создал валидный XML с23 pilot nodes; MIUI вывела warning
о missing theme_compatibility.xml, но XML получен. Прежнего endless idle timeout нет.
После expiry revision8 **12:58:55UTC** UI VPN off, обе pilot services отсутствуют.
Установленные версии: pilot0.1.4-beta05/code5 и исходный0.1.0/code1.

Удалены временные Android peers. С pre-test receipts сверены все исходные WG3/AWG1
peers: значения сохранены. Отдельный family-connect-android-tcp-pilot остановлен и
удалён; его timer и WG/AWG timers остановлены. Private backup/config/receipt directories
сохранены. Существующие service StartedAt не изменились:

- AWG gateway2026-09-10T21:02:48.155055691Z;
- TCP443 gateway2026-09-11T13:18:55.24780161Z;
- product API2026-09-10T11:10:53.139051801Z;
- новый постоянный HTTPS ingress2026-09-14T11:14:20.720039078Z.

UI helper /data/local/tmp/fc-ui-dump.jar, /data/local/tmp/fc-ui-beta05.xml и JDWP
forward tcp8700 удалены; adb usb подтвердил restarting in USB mode. Проверка5555
вернула connection refused111. Телефон можно погасить. Private native keys/journal,
исходное приложение и HTTPS ingress сохранены. Последний committed hashconfig8:
fdc106fed72d7ce6a3199fe3c2cfd96436abff1544122829142c74ab21348bd9; следующий sequence>8.
Не сбрасывать journal и не переиспользовать уже опубликованные revisions.

Осталось: российские AWG/TCP сети и blocked-WG managed Auto; AWG3.1 signed schema;
отказ relay/полного gateway и независимый путь доставки; Doze, Wi-Fi/mobile handover,
полный routing/IPv6/DNS cleanup, длительные/многопользовательские проверки; Windows
native Stage5 и общий выпуск трёх платформ. Short beta05 retry series не доказывает
устранение всех transient сетевых отказов. Scheduled TLS renewal ещё не наблюдался.
Django/платежи после VPN, messenger/iPhone отложены. Это техническая device acceptance,
не публичный платный релиз и не заявление о доступности из России.

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
[Rollout/rollback](../../deploy/friends/README.md).

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
