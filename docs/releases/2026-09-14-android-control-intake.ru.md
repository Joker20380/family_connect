# Android Stage 5: explicit signed-file intake — 14.09.2026

## Изменения

Продолжение регистрации. HEAD4cb1423/main и прежний незакоммиченный Stage5 сохранены.
Сверены ControlRelay/Reticulum carrier и product provisioning. /v2/provisioning/fetch
выдаёт другой envelope; его нельзя напрямую подавать в Stage5 control.receive.
Native RNS transport в Android пока отсутствует. Этот блок завершает явный локальный
путь «выбранный signed file → service owner → verifier/journal → apply → health»;
не заявляет автоматическую сетевую доставку.

Добавлен ControlIntake: bounded read и копирование непустого envelope ≤65536 bytes.
Ошибка provider, превышение лимита, отсутствие progress и прерывание read отказывают.
Это ограничение байтов, не доказанная граница времени для зависшего content provider.
Byte array отделён от исходного потока до dispatch; URI/path в службу не передаются.

Intake требует валидные enrollment fields/schema, ENROLLED, null proof, HTTPS origin
и совпадение device с локальной Reticulum identity. Далее используется прежний
ControlTransaction.receive с offline packaged anchor и текущей package version.
Plaintext profile, неверная подпись/identity/WG/version/time/replay не обходят verifier.
Последовательность snapshot/stage/apply/health/commit/ACK и crash rollback сохранена.
Если receive вернул COMMITTED для дубликата после остановки engine, вызывается
существующий safe resume с проверкой локальных profiles и traffic health. Нового
profile apply/revision/commit/ACK из-за resume не возникает; уже работающий engine
повторно не запускается. Recovery-only и startup resume продолжают прежнюю семантику.

ConnectionService принимает внутреннее действие apply-control только до начала
сессии; active/stopping/closing возвращают BUSY без замены живого VPN. Получение
owner согласовано с enrollment/import/clear. При отказе claim восстанавливается
предшествующий status (для нового intake это off), чтобы не зависнуть на connecting.
Служба по-прежнему non-exported. Anchor из Intent не принимается. Применение идёт
на том же worker/engine. Cancel/revoke/ошибка shutdown сохраняют прежние запреты
reconnect и удержание owner. При отсутствующем engine после результата служба завершается.

## UI

Отдельная кнопка «Применить подписанную конфигурацию VPN», доступна при остановленной
сессии. Пользователь подтверждает, что выбирает encrypted signed config для своего
устройства и что после успешного применения VPN подключится. Используется
ACTION_OPEN_DOCUMENT, bounded read на worker, затем системное VPN permission и
notification permission. Результаты COMMITTED/REJECTED/ROLLED_BACK/FAILED/BUSY имеют
отдельный текст RU/EN. Результат в UI — наблюдение сессии, не новая авторизация.

Pending envelope хранится только в памяти Activity; не включается в savedInstanceState,
не копируется в preferences/профили и не получает persistable URI permission.
При recreation/destruction/отказе VPN permission pending пропадает; пользователь
выбирает файл заново. Notification callback без pending не начинает legacy connect.
Применение уже запущенное в Service не зависит от дальнейшей жизни Activity.
Реальные picker/rotation/permission/revoke/back и layouts ещё требуют Android runtime.

## Проверки

Docker gradle:8.11.1-jdk17 --network none, Android35, BC1.85.2/Gson2.13.2/JUnit4.13.2.
Aapt2 compiled/linked RU/EN resources и fresh R.java (temporary manifest package),
все app Java и local test Java скомпилированы с cached previous engine/R dependencies.
Resource-only package не является собранным application APK. Full Gradle/lint/ABI,
Android Keystore/AtomicFile/service/UI runtime и настоящее VPN connection не приняты.
Прежние missing annotation Scope.LIBRARY_GROUP warning/VpnHealth deprecated note остались.

**91 Java tests passed,2.493s**: прежние81 и10 ControlIntakeTest. Проверены границы
0/65536/65537 и byte copy, provider/read failure и interrupt, действительный envelope
с commit/ACK, plaintext/другой envelope без profile writes, unfinished/foreign enrollment,
cold duplicate resume без перезаписи, обязательный health при resume, pending crash
rollback до повторного apply, expiry/cancel без reconnect. Используются настоящий
identity/verifier/journal и fake native Host; это не Android OS acceptance.

Прежние30 config/15 ACK/32 structural/4 cipher refusals прошли; manifest SHA256
c97e00ccff7440b09a636a792557c0602aba5eb63815cdc8fefe7755711ac3cd.
Python/API/fixtures не менялись;57 Python tests предыдущего блока не повторялись.
Harness: /tmp/fc-android-intake/check.sh; portable:
`gradle -p clients/android/control-tests test`.

## Версии, rollout и оставшаяся работа

VersionCode3/versionName0.1.2-beta03 сохранены. Последняя локально документированная
Android сборка CI34776015693/source63831305f063350fd21af44c93d6a8bef122b795:
APK SHA256 c6bb7df99d55a53a8da0d7fb9f177855976d91c6cf8b8bb1adf1fb652399649a.
Она не содержит новых исходников. Remote CI/release/deployment этой сессией
не проверялись. Нет нового application APK, установки, commit/tag/release/catalog,
выдачи live signed config или изменений серверов.

Для будущей isolated acceptance: зарегистрированная device identity; offline-signed
Stage5 schema2 envelope, выданный именно ей и её WG key, действующие lease/time и
реальный Android minimum version; остановленная сессия; разрешение VPN; выбор файла.
Desktop fixture minimum0.2.9 не подходит нынешнему Android0.1.2 — этот отказ сохранён.
Не использовать PUBLIC TEST ONLY keys/fixtures для live enrollment или конфигурации.
Никаких live ключей/профилей этой сессией не читалось и не выводилось.

ACK сохраняются в bounded outbox; автоматической доставки/экспорта здесь нет.
Нужны native RNS carrier с challenge/fetch и ACK retry без отключения рабочего VPN,
полный Android runtime и packaging trust resource/minimum-version acceptance.
Также остаются managed Auto/AWG3.1, manual admission и условия выпуска трёх платформ.
Django/оплата и Messenger/iPhone не начинались этим блоком.

## Source rollback

Stage: /tmp/fc-android-intake/tree; snapshot: /tmp/fc-android-intake/before.
Перенос проверяет SHA256 исходников/отсутствие новых destination files и сохраняет
остальную незакоммиченную работу. Для возврата восстановить MainActivity,
ConnectionService и RU/EN strings из snapshot, убрать ControlIntake/ControlIntakeTest,
обновить STATUS/PLAN. Enrollment gate/identity/journal/криптографические ключи
не удалять, replay floor не снижать. Уже созданные ACK/pending/committed нужно
сохранить при любом откате исходников. Runtime rollout отсутствует.
