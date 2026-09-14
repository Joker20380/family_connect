# Android CI и защищённое состояние — 2026-09-14

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
