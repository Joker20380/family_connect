# PINNED-EVIDENCE-CORRELATION-1 — PASS

06.10.2026. Только исходники и локальные тесты. Это результат проверки контракта
корреляции, а не acceptance новых APK/JNI/gateway, физического эксперимента или
публичного релиза. SOURCE FREEZE НЕ ВЫПОЛНЕН; коммит не создан. Установленный
sealed beta66/code66 и baseline `5327deb414ae8aa77ce2f9490fd99c9485eba740` не менялись.
Текущий HEAD рабочей ветки `8d046321039d0bd1e18ecc1af979ff90f591e029` НЕ содержит
эту незакоммиченную дельту и не является её provenance-коммитом.

Ничего не собрано для распространения, не подписано, не установлено и не развёрнуто.
Не обновлялись credentials, не запускались Telemost, физическая сессия/fault,
контакты с тестером или CI публикации. Компиляция тестовых Go/cgo/JVM-программ —
часть локальной проверки, не создание кандидата. DATA19 recovery не перепроверяется;
OWNER-CONTROLLED-LOSS-1 остаётся FAIL / UNKNOWN.

## Причина прежней неоднозначности

Legacy receiver watch сравнивал logical seq, но игнорировал attempt, привязывался
к первому carrier message и завершался до достоверного определения попытки.
После COMPLETE поздний selected retry уже не мог изменить доказательство.
Старый API `EnableEvidenceWatch(rx, ...)` теперь отвергается. Его receiver-тест
заменён проверкой отказа; сценарий late attempt0 сохранён и усилен в новых тестах.
Legacy sender-watch остаётся дополнительной диагностикой, но не receiver authority.

## Новый контракт pinned-correlation-v1 / schema 1

Ключ: session tag из действующего Recorder, каноническое направление
`client_to_gateway` либо `gateway_to_client`, uint64 Reliable sequence,
attempt 0..32 и 128-битный случайный generation/nonce (32 hex символа).
Session tag — существующий непрямой диагностический идентификатор, не credential.
Номер попытки не добавляется в Reliable/carrier/VP8/RTP или Family TLS payload.

На receiver операция `prearm` принимает пустой generation и создаёт свежий nonce.
Возвращается ARMED receipt с полным ключом и `expires_at_ms`. На sender оператор
передаёт точно этот ключ, включая nonce. Роль endpoint фиксирована кодом:
gateway/client; локальное tx/rx выводится из роли и канонического направления,
не принимается от управляющего клиента. Внутренний Go API используется тестами.

Один выпуск watch на направление/Recorder; максимум два watch. После terminal
остаётся только bounded tombstone ключа/состояния, повторный prearm этого направления
отвергается. Следующая сессия получает новый Recorder и новый nonce. Это намеренно
строже, чем разрешение повторного arm внутри той же сессии.

Состояния: ARMED → BOUND → COMPLETE; EXPIRED/CLEANED/CLOSED/OVERFLOW/CONFLICT —
terminal. Sender может перейти ARMED → COMPLETE после формирования descriptor.
COMPLETE означает **точную выбранную media/carrier-попытку**, не доказательство
Reliable ordered consumption, ACK, HTTPS либо отсутствия дальнейшего exhaustion.
Отдельного состояния CONSUMED нет: BOUND означает одноразовое потребление descriptor,
после чего второй bind отвергается даже до COMPLETE.

### A. Ограниченный предварительный сбор

До descriptor receiver сохраняет максимум четыре отдельных carrier identity
`(sender,message)`; у каждого максимум восемь fragment slots, соответствующих
существующему carrier maximum. У каждого fragment хранятся index/count, VP8
PictureID, RTP timestamp, inclusive modulo-65536 sequence range и packet count.
Также сохраняются времена первого/последнего наблюдения, реконструкция фрагмента
и завершение carrier message. Никаких payload bytes, адресов или free-text.

Fragment0 определяет logical seq; фрагменты, пришедшие раньше fragment0,
удерживаются как неизвестные кандидаты. Когда становится известен чужой seq,
такой provisional candidate удаляется; фиксированный 64-slot exclusion cache
отсекает его последующие фрагменты. Это не обычный evidence ring. Нехватка четырёх
candidate slots приводит к OVERFLOW с очисткой, а не к вытеснению выбранного
доказательства или предположению о номере попытки. Конфликт media identity одного
fragment даёт CONFLICT. Транспорт продолжает работать независимо от этой ошибки.

Совпадение seq само по себе никогда не переводит receiver в COMPLETE. Не выбранные
carrier identity сохраняются отдельно; неизвестный номер их попытки не выдумывается.
Для именования конкретного nonselected identity как attempt0/attempt2 нужна
сторона отправителя; тесты знают этот источник. Для исключения их из attempt1
достаточно несовпадения с authenticated selected descriptor.

### B. Descriptor и точная привязка

Sender фиксирует identity выбранной попытки из существующего carrier_queued или
pre-write carrier_written/incomplete callback. Последний закрывает гонку, когда
writer опережает квитанцию очереди. Это только наблюдение; очередь/отправка не ждут
управляющий канал. До получения RTP write metadata **всех** фрагментов descriptor
не публикуется. Identity sender/message одной выбранной попытки неизменна.

Descriptor содержит полный ключ, sender/message и упорядоченный набор MediaIdentity
для всех fragments. Каждый включает PictureID, timestamp, first/last RTP sequence
и packet count. Оператор получает его через `status` sender и передаёт receiver
через `bind`. Descriptor допускается после фактической packetization/emission:
provisional storage сохраняет доказательства до его получения, независимо от ring.

Receiver принимает только один descriptor с полным точным ключом. COMPLETE требует
одного candidate с тем же sender/message, подтверждённым logical seq, carrier
completion, всеми реконструированными fragments и полным совпадением MediaIdentity.
Fragment0 attempt0 + fragment1 attempt1 не образуют единый candidate. Duplicate
того же identity идемпотентен; другая попытка не заменяет выбранную. Wrong session,
generation, direction, seq, attempt и replay отвергаются без изменения watch.

Receiver RTP identity снимается отдельным diagnostic-only наблюдателем **после
существующего reorder**, перед существующей VP8 reconstruction. Сырой callback/ring
не меняется. Это устраняет зависимость агрегированного range от порядка прихода
пакетов; reorder algorithm, packetization и data flow не изменяются.

В локальном Pion совпадают все PictureID/timestamp/ranges. Если реальный relay
переписывает RTP/VP8 identity, текущий контракт не маскирует это: watch не завершится.
Ослабление сравнения или преобразование namespace автоматически не разрешено.
Поведение внешнего relay этой задачей не проверено.

## Аутентифицированное runtime управление

### Gateway / Linux

Только `fc_owner_diagnostic`: optional `FC_DIAGNOSTIC_CONTROL_DIR`, заранее созданный
оператором каталог mode0700, принадлежащий effective UID процесса, без symlink на
самом каталоге. На сессию создаётся `<session-tag>.sock`, mode0600. `SO_PEERCRED`
проверяет тот же effective UID. Нет TCP listener, public HTTP route, bearer token
или расширения Family TLS. Root/оператор может выполнять операции от UID процесса
через уже авторизованный административный доступ; новые credentials не нужны.

Регистрация реально подключена к roombroker gateway и wholedevice client после
bootstrap, на lifetime dedicated-сессии, а не краткого descriptor request.
Она не оставлена только тестовой функцией. Без env socket не создаётся. Listener
привязан к session context; его отмена закрывает контроль и очищает watch.
Один connection обрабатывается последовательно, deadline1s, запрос ≤16KiB,
строгий JSON с отказом unknown fields/trailing data. Клиент завершает write-half,
затем читает один JSON receipt. Ошибки возвращают только `rejected`.
Stale socket после аварийного завершения не перезаписывается автоматически:
ошибка старта означает отсутствие канала, не permission обходить prearm.

### Android ownerDiagnostic

Используется существующий `OwnerFaultReceiver`, защищённый
`android.permission.DUMP` и отсутствующий в публичных flavor manifests.
Новая операция `command=correlation`, `request=<JSON>` маршрутизируется через
существующий JNI `control` / `fcRestrictedFault`; JNI ABI и C bridge не изменены.
Native выбирает Recorder именно текущей session под существующим owner lock;
роль жёстко `client`. Нет current session — rejected. Java ограничивает body,
Go повторно проверяет UTF-8 byte length и строгий JSON. Fault arm/status/disarm
сохраняют прежний контракт; correlation не вызывает fault arm.

### Граница доверия

Descriptor переносит доверенный оператор: same-UID Unix caller на gateway и
DUMP-authorized caller на Android. Receipt sender служит источником identity;
передача между этими административными endpoint выполняется вне user data plane.
Отдельной end-to-end подписи descriptor нет. Это OS-authenticated operator control,
а не защита от злонамеренного root, same-UID процесса или самого уполномоченного
оператора. Недоверенный peer/network payload не может выдавать команды управления.
Nonce не является паролем; он предотвращает stale/cross-session binding, а не
заменяет аутентификацию endpoint. Будущий harness обязан сохранять обе квитанции
prearm, исходный sender descriptor и receiver result; fallback на legacy rx запрещён.

## Очистка, время жизни, изоляция

TTL30s фиксирован: проверяется на каждом событии/запросе и отдельным diagnostic
таймером, в том числе в idle и после COMPLETE. По timeout, явному cleanup, закрытию
или context cancellation удаляются candidate media, descriptor, identity и exclusion
cache; остаётся только bounded terminal key/state. Если есть legacy sender-watch
для той же выбранной попытки, он также очищается. Не относящийся к ней sender-watch
не затрагивается. Ничего не восстанавливается с диска после restart.

Новые API реализации/состояние/Unix listener компилируются только с diagnostic tag.
Default имеет no-op hooks и `disabled` command stub: arm/bind невозможны; новый
schema не попадает в Snapshot/Delivery и дополнительных default telemetry нет.
Сравнение относится к исходному состоянию этого задания, не переаттестует старые
изменения обычного boundary instrumentation из предыдущих задач.

Reverse DATA104 не исправлялся. Направление входит в каждый key и descriptor,
peer-local tx/rx проверяется отдельно; reverse lifecycle не может занять selected
forward candidate. Новый полноценный DATA104 lifecycle channel здесь не заявлен.

## Локальные проверки

Логи и manifests: `state-client-build/field65-export16/pinned-evidence-correlation-1/`.
Go dependencies — существующий offline cache, Go1.26.0; локальные Unix/HTTP tests
потребовали согласованного запуска вне sandbox. Внешние сети не используются.

| Проверка | Результат |
| --- | --- |
| C1 late attempt0 | PASS: до descriptor только ARMED, после attempt1 descriptor — BOUND, после выбранных media — COMPLETE |
| C2 selected descriptor | PASS: только точный key и выбранные sender/message/media |
| C3/C4 duplicates | PASS: original/retry, RTP/VP8 observations и carrier duplicates не меняют выбранную попытку |
| C5 fragments | PASS: reordered fragment capture, отдельные slots; cross-attempt mixing не завершается |
| C6 attempt2 | PASS: отдельный identity не удовлетворяет attempt1 |
| C7/C8 replay/session | PASS: stale/replayed descriptor и wrong generation/session/direction/seq/attempt отвергаются |
| C9 cleanup | PASS: provisional/pinned state и совпадающий legacy sender очищаются |
| C10 timeout/restart | PASS: expiry, idle timer без status, fresh generation после нового Recorder |
| C11 retention | PASS: 2,100 unrelated boundaries в matrix; local Pion single/multi после2,000 |
| C12 default | PASS: no-op endpoint/command, неизменный JSON telemetry, public source isolation |
| C13 privacy/bounds | PASS: enum/numeric-only metadata, strict request, finite candidates/fragments, overflow fail-closed |

Default Go и diagnostic race: sessiontrace, reliablestream (включая существующие
ACK semantic tests), telemost и roombroker; отдельно default/race wholedevice.
Дополнительно verbose tagged race для
correlation/legacy rejection/Pion. Pion scenarios: normal, late_message, late_rtp,
duplicate и reordered RTP; попытки0/1/2, все три fragments, отдельный single-fragment
watch test. Проверяется неизменность RTP bytes после diagnostic observer.
Python privacy/bounds/packaging/source-guard:13 PASS. `git diff --check`: PASS.

Android/JNI: owner receiver компилируется против Android35 API; JVM fixture
проверяет маршрутизацию/ограничения; host cgo smoke исполняет текущий fcRestrictedFault
с обеими build-tag конфигурациями, заменён только Android build constraint для
host fixture. C JNI ABI не менялся. Проверка всего старого bridge с host JDK/GCC
выявляет существующее несовпадение AttachCurrentThread pointer type; compatibility
syntax check проходит с понижением этой host-only ошибки до warning. Этот участок
не менялся. Это НЕ NDK/arm64 runtime acceptance и не сборка JNI .so/APK. Native
platform acceptance и signer/artifact provenance относятся к следующей задаче.

## Изменённые исходники и ограничения поставки

`source-delta.json` фиксирует начальные SHA256 scoped файлов; `before.json` —
исходные dirty файлы. `final-source.json` фиксирует итоговые хеши проверяемой дельты.
Это локальная атрибуция, не source freeze и не подмена commit provenance.

Область: sessiontrace correlation implementation/control/tests и recorder hooks;
telemost diagnostic observer/Pion tests; roombroker/wholedevice registration hooks;
ownerDiagnostic Java routing; native fault-command routing; Python source guard;
STATUS/PLAN и этот отчёт. Reliable stream/wire, retry/RTO/pacing, fragment encoder,
VP8 encoding, packetizer, ACK и Family TLS application не изменены этой дельтой.
Существующие несвязанные dirty файлы сохранены. Ни staging index, ни sealed source
не изменены. Нет нового commit/tag/version, APK/JNI/gateway hashes или signing.

Откат runtime не требуется: runtime не менялся. Откат исходников — только scoped
дельта этого задания по сохранённым baseline hashes; не `git reset` всего дерева.

Результат позволяет **начать отдельную задачу candidate freeze/acceptance**.
Не разрешает автоматически сборку здесь, deployment, impairment или физический
запуск. Это не повышает прежний полный PINNED-EVIDENCE-CANDIDATE-1 до PASS: полноту
всех stage/export/lifecycle требований следует проверить при подготовке кандидата.

Ровно один следующий шаг: отдельная задача чистого scoped source freeze и полной
приёмки диагностического кандидата на основе этого контракта, без автоматического
перехода к физическому эксперименту.
