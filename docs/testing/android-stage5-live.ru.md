# Android Stage5: приёмка на реальном устройстве

Текущее состояние, версии и реальные результаты: [STATUS](../STATUS.md) и
[отчёт14.09.2026](../releases/2026-09-14-android-storage-runtime.ru.md).
[Sanitized receipt](../android-stage5-live-result.json) относится к указанному в нём APK.
Проверка эмулятора и успешный CI не означают установленную сборку или приёмку РФ.

## Подготовка

1. Проверить source SHA и успешные platform CI, скачать artifact, сверить digest,
   native ABI, Python/RNS, packaged anchor/bootstrap/licenses. ARM64 selection не
   меняет retained payload; после zipalign подписать постоянным локальным beta key.
   Не подписывать failed CI artifact и не менять bytes опубликованной версии.
2. Проверить реально установленную версию и сертификат. Debug pilot имеет ID
   `com.familyconnect.app.pilot`; исходный `com.familyconnect.app` сохраняется.
   Обновление pilot должно сохранять его identity/journal и использовать тот же
   signing key с большим versionCode. Не удалять app data для обхода ошибки recovery.
3. Оставить телефон разблокированным для системного VPN consent. Проверить ADB;
   Wi-Fi ADB при нестабильном USB включать временно и вернуть `adb usb` после теста.
   `ControlStorageRuntimeTest` с destructive disposable fixtures предназначен
   только для эмулятора; на реальном телефоне его не запускать.
4. Записать страну/оператора/тип сети. Европейский телефон проверяет runtime цепочки,
   но не доступность из РФ. Для сетей пользователя, где WG блокируется, обязательны
   отдельные AWG/TCP прогоны и проверка недоступного WG.

## Основная цепочка

Регистрация через UI: `https://185.251.89.19:8443`, отдельное одноразовое приглашение.
Нативная identity создаётся на телефоне; серверная binding запись должна подтвердить
устройство и его публичный WG key. Token/private keys/профили не копировать в отчёт.
До создания приглашения сохранить private product DB backup; общий restore DB не
является способом отката одного тестового пользователя.

Подготовить отдельный временный peer/credential на разрешённом gateway и timer его
удаления. Сохранить соседние peers/clients. В подписанной конфигурации WG private key
заменён на `LOCAL_DEVICE_KEY`; реальный ключ подставляет сам клиент. TCP credential
требует private handling. Offline signing root остаётся локальным.

[Порядок relay](../reticulum-control.ru.md): новая revision строго выше journal floor;
previous hash указывает на последний **committed** envelope, включая случай, когда
более свежая попытка откатилась. Не перепубликовывать тот же sequence с другими bytes.
После сбоя сверять публичные подписанные ACK перед выбором следующей revision.

В UI выбрать «Подключить через Reticulum» и подтвердить системное разрешение VPN.
Для каждого WG/AWG/TCP прогона проверить:

- Получен encrypted signed envelope для этого устройства; подпись/anchor/version/
  previous hash/lease проверены нативным verifier.
- На relay проверены device signatures RECEIVED → APPLIED → COMMITTED, exact hash
  и revision; один APPLIED или поднятый TUN не считается успешным подключением.
- DNS и HTTPS идут через конкретный VPN Network; «Проверить внешний IP» показывает
  egress выбранного gateway. Отдельно сверить handshake/счётчики нужного WG/AWG peer.
- Повтор того же envelope не создаёт новую apply transaction. Успех одного запроса
  не заменяет устойчивость, IPv6/DNS/route cleanup и длительный тест.

Managed schema2 пока допускает AWG2, а AWG3.1 отклоняет. Наличие AWG3.1 engine не
означает принятую подписанную схему3.1. UI transport slot сам по себе не доказывает версию.

## Сбои

| Сценарий | Условие успеха |
|---|---|
| Force-stop committed pilot → новый процесс → явный connect | Прежняя identity/config, реальный Internet, без новой регистрации/apply transaction |
| Подписанная конфигурация с недоступным endpoint | ROLLED_BACK/HEALTH и Internet через предыдущую рабочую конфигурацию |
| Остановка после durable APPLIED_PENDING до COMMITTED | После запуска ROLLED_BACK/RECOVERY; сохранённые ACK доставлены из outbox; рабочая конфигурация восстановлена |
| Истечение принятой lease | Туннель остановлен, expired config не поднимается при новом connect; прежние ключи/journal сохранены |
| Отказ relay при живом VPN | VPN продолжает работать до lease; ACK не потеряны, sync восстанавливается |
| Недоступный WG, затем AWG; недоступный UDP, затем TCP | Реальные bound DNS/HTTPS и один владелец туннеля после переключения; проверять реализованную managed Auto policy отдельно |
| Sleep/Doze, Wi-Fi/mobile handover | Предсказуемое восстановление либо явный отказ без ложного статуса Internet |

В debug pilot точная crash-точка может задаваться JDWP breakpoint в
`ControlApplication.healthy`: в новом receive вызов следует после сохранения
APPLIED_PENDING. Сначала подтвердить достижение точки, затем `am force-stop` только
pilot package. Не читать значения ключей/профилей через debugger. Отладка влияет на
тайминг, поэтому её успешный reconnect не объясняет исчезнувший без отладчика сбой.

Health probe имеет общий15s budget; отмена и поздний успех не должны приводить к
commit. Общая задержка RNS/подписей/записи журнала не равна длительности этой пробы.
Отказ краткой конфигурации до COMMITTED не проверяет автоматический expiry stop.

## Завершение

Сохранить exact APK/source/hash, сеть, ACK outcomes, внешний IP, сбои и незавершённые
проверки в STATUS/PLAN/датированном отчёте. Завершить pilot VPN, удалить только его
временные peers/containers и остановить связанные timers; проверить исходные peers
и services. Сохранить private receipts и journal для следующей revision.
Убрать временный UI helper/JDWP forwarding и закрыть Wi-Fi ADB. Исходное приложение,
product DB и долгоживущий HTTPS ingress не удаляются при уборке VPN pilot.
