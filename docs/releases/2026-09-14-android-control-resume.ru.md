# Android Stage 5: explicit committed resume — 14.09.2026

## Реализация

Продолжение startup recovery; исходный HEAD4cb1423/main и большой незакоммиченный
Stage5 сохранены. Добавлен ControlTransaction.Resumable и отдельный resume:
под существующим owner читается/проверяется journal, pending запрещает resume,
committed envelope проверяется на текущие trust/device/WG/version/time constraints.
До start сохраняется clock floor. После health подпись/lease/clock проверяются
повторно и last_now сохраняется; только после этого возвращается RESUMED.
Committed/revision/floor/result/outbox не заменяются. Empty committed даёт IDLE.

ControlApplication.resume требует остановленный engine и проверяет все signed slots
на точное совпадение с materialized config, включая собственный WG key из identity.
Выбирается первый signed transport, как при apply. Профили не перезаписываются;
изменённый/отсутствующий slot отклоняется, автоматического ремонта нет. Чужие slots
сохраняются. Cancel/revoke блокируют start; используется тот же service host/engine,
network-bound DNS/HTTPS и lease timer. Failure после попытки resume вызывает stop;
ошибка stop сохраняется как suppressed error, service cleanup удерживает owner
при неуспешном shutdown.

ControlStartup вызывает resume только при явном connect и результате recovery IDLE.
Recovery ROLLED_BACK не начинает ещё одно подключение. Null Intent не запускает
committed resume. Managed ветка не переходит к legacy/Auto. Импорт/очистка по-прежнему
блокируются managed gate. Recovery-only dispatcher не меняет своей семантики.

Crash во время resume не создаёт частичных profile writes: их в этом пути нет.
Durable journal остаётся IDLE с прежним committed. Освобождение engine при смерти
Android-процесса требует отдельной OS acceptance, не доказывается portable tests.
START_NOT_STICKY сохранён: это следующий явный запуск, не boot/autorestart feature.

## Проверки

Контейнер gradle:8.11.1-jdk17 без сети, Android35, cached previous-app classes/R.jar;
BC1.85.2/Gson2.13.2/JUnit4.13.2. **63 Java tests passed,2.155s**:
прежние50,2 startup admission и11 resume test methods. Сценарии: сохранение journal/
profiles/ACK, empty committed, expiry/clock regression до и после start, mismatch/
missing slot, health/cancel/revoke, pending recovery, corrupt digest/wrong trust,
write failure до activation и после health с retry, simulated process death,
foreign owner. Native host в тестах fake; identity/verifier/journal настоящие.

Первоначально harness не компилировался из-за наследования final test Host,
затем из-за helper с прежним типом Host; исправлено только устройство тестового
fixture. Финальная компиляция всех app Java прошла. Сохранены прежние warning
unknown androidx.annotation.RestrictTo$Scope и note VpnHealth deprecated API.
Full Gradle/lint/ABI/resources, OS Keystore/AtomicFile/VPN/process-death acceptance
не проводились. Python не менялся, suite не повторялся.

Неизменённые 30 config/15 ACK/32 structural/4 cipher refusals прошли; manifest SHA256
c97e00ccff7440b09a636a792557c0602aba5eb63815cdc8fefe7755711ac3cd.
Harness: /tmp/fc-android-resume/check.sh; portable tests:
`gradle -p clients/android/control-tests test`.

## Identity и product plane

По уточнению пользователя клиент привязан к криптографической Reticulum identity.
Проверены существующие ControlIdentity.proveTransportKey и ProductStore.enroll:
RNS proof связывает public identity, отдельный WG public key, challenge и audience;
сервер сверяет одноразовый challenge и entitlement. Это уже существующий protocol,
новая регистрация этой сессией не выполнялась. Django/PostgreSQL предложены для
кабинета/оплаты; отдельный entitlement adapter сохраняет проверенный FastAPI product
API. Prometheus — технические метрики, транзакционная БД — платежи.
[Дизайн и порядок интеграции](../design/django-product-plane.ru.md).

## Версии и оставшаяся работа

VersionCode3/versionName0.1.2-beta03 сохранены. Последний локально документированный
Android CI34776015693/source63831305f063350fd21af44c93d6a8bef122b795 относится к
предыдущему APK, SHA256 c6bb7df99d55a53a8da0d7fb9f177855976d91c6cf8b8bb1adf1fb652399649a.
Remote release/deployment в этой сессии не проверялись. Нет нового APK, установки,
commit/tag/release/catalog, выдачи live config или изменений серверов.

Далее explicit enrollment/identity+WG binding/init journal, управление manual edits
после recovery, packaging trust/minimum-version policy и Android runtime acceptance,
RNS carrier, runtime managed Auto/AWG3.1. Desktop fixture minimum0.2.9 всё ещё
не подходит Android0.1.2; версия не подменяется. Django пока только дизайн.
Messenger/iPhone остаются отложены до полного плана VPN трёх платформ.

## Перенос и возврат

Stage: /tmp/fc-android-resume/tree, исходный snapshot: /tmp/fc-android-resume/before.
Перенос проверяет исходные SHA256 и отсутствие новых destination files, сохраняет
остальной незакоммиченный Stage5. Для source rollback восстановить ControlTransaction,
ControlApplication, ControlStartup, ConnectionService и ControlStartupTest из snapshot,
убрать ControlResumeTest; документацию привести к фактическому состоянию. Не удалять
device identity/journal, не снижать replay floor. Runtime rollback не нужен: установки
не было. Git diff --check и byte equality проверяются после переноса.
