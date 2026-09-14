# Android Stage 5: startup recovery — 14.09.2026

## Изменения

Продолжение application adapter. Исходный HEAD 4cb1423, main; существующие
незакоммиченные изменения сохранены. ConnectionService после получения owner
проверяет control identity/journal base/bak/new и aliases. При managed state
синхронно вызывает общий controlNow/recover на существующем worker, не ставит
восстановление в очередь позади обычного connect. Тот же метод используется
внутренним dispatcher; packaged trust, package version и journal verifier сохранены.

Новый ControlStartup определяет порядок admission. Только отсутствие managed state
и явная команда connect разрешают legacy/Auto. IDLE/ROLLED_BACK завершают managed
ветку без перехода к ручному профилю. Неизвестный результат/FAILED/ошибка чтения
приводят к существующему stop/cleanup. Незавершённый journal сохраняется для retry;
ошибка engine shutdown по-прежнему удерживает owner. Если recovery восстановил
допустимый baseline engine, служба продолжает monitoring и lease timer. Если engine
нет, служба завершается. Disconnect по-прежнему обрабатывается до admission,
cancellation/revoke запрещают reconnect через существующий application host.

Проверка presence выделена в boolean метод; requireUnmanaged и import/clear gate
сохранены. Файлы и ключи не создаются и не удаляются при admission. Ошибка Keystore
не трактуется как отсутствие состояния. Null Intent/команда без connect больше
не запускают обычный WG. Все существующие Android runtime callers используют
явный connect. Служба остаётся START_NOT_STICKY: автозапуск при загрузке устройства
и автоматический перезапуск после process death не добавлены; восстановление
происходит при следующем запуске службы.

## Проверки

Docker gradle:8.11.1-jdk17, --network none, Android35, cached engine classes/R.jar,
BC1.85.2/Gson2.13.2/JUnit4.13.2. Все app Java и локальные test Java скомпилированы.
**50 JUnit tests passed, 1.875s**, включая 7 новых ControlStartupTest:
explicit unmanaged connect; managed IDLE/rollback без legacy fallthrough; недоступный
Keystore; failed/unknown recovery; crash/restart с реальным journal/core и сохранением
floor; failed rollback с последующим retry; committed state без повторного apply и
потери ACK. OS host в этих проверках не настоящий Android runtime.

Прежние 30 configuration/15 ACK/32 structural/4 cipher refusals прошли. Manifest
SHA256 c97e00ccff7440b09a636a792557c0602aba5eb63815cdc8fefe7755711ac3cd.
Сохранены прежний missing androidx.annotation.RestrictTo$Scope warning и VpnHealth
deprecated API note. Full Gradle/lint/ABI/Keystore/AtomicFile/process-death/VPN
runtime не проверены. Python/fixtures не менялись, Python suite не повторялся.
Harness: /tmp/fc-android-startup/check.sh. Portable suite:
`gradle -p clients/android/control-tests test`.

## Версии, выпуск и оставшиеся задачи

VersionCode3/versionName0.1.2-beta03 сохранены. Последний локально документированный
Android artifact: CI34776015693, source63831305f063350fd21af44c93d6a8bef122b795,
APK SHA256 c6bb7df99d55a53a8da0d7fb9f177855976d91c6cf8b8bb1adf1fb652399649a.
Это предыдущая сборка; новые изменения в неё не входят. Remote CI и deployment
в этой сессии не проверялись/не запускались. Нет commit/tag/release/catalog,
нового APK, установки или серверных изменений.

Startup recovery подключён в исходниках, но Stage5 не завершён. IDLE committed
config намеренно не переприменяется: нужен отдельный безопасный resume с проверкой
lease, подписанного профиля, health и crash semantics. Explicit enrollment с WG
binding/init journal, разрешение manual edits после recovery, runtime acceptance,
platform minimum-version policy, packaging trust check, RNS carrier, runtime Auto
и managed AWG3.1 остаются открытыми. Messenger и iPhone отложены согласно PLAN.

## Source rollout и rollback

Изменения подготовлены и проверены в /tmp/fc-android-startup/tree; перенос в основной
репозиторий проверяет SHA256 каждого изменяемого исходного файла, чтобы не затереть
параллельную работу. Снимок до переноса: /tmp/fc-android-startup/before.
Для source rollback восстановить ConnectionService/ControlMutationGate/
ControlStatePresence из этого снимка, убрать новые ControlStartup и ControlStartupTest,
сохранить остальной Stage5. Документацию обновить по фактическому результату.
Не удалять identity/journal, не снижать replay floor. Runtime rollback здесь отсутствует:
новая сборка не устанавливалась.
