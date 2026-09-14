# Android Stage 5: общий service/profile owner — 14.09.2026

## Исходная точка и результат

Продолжение после journal/ACK checkpoint по запросу пользователя. STATUS/PLAN,
AGENTS, git status и существующие ConnectionService/MainActivity/ProfileStore
проверены. Базовый HEAD4cb1423/main, существующее большое незакоммиченное дерево
сохранено; messenger/iPhone остаются отложенными до всех условий трёх платформ.

Найдена граница интеграции: импорт профиля шёл в worker Activity, а VPN start/Auto/
cleanup — в worker службы. Проверка static UI status не обеспечивала атомарное
взаимоисключение. Добавлен process-local владелец сессии и реальные точки его
использования; Stage5 application/recovery ещё не включены в живой VPN.

## Изменения

- ControlOperations использует тот же ControlJournal.OWNER. Session lease остаётся
  между callbacks, пока движок не остановлен с существующим awaitShutdown barrier.
  Release требует точный token; stale callbacks и старая служба не могут изменить
  или освободить нового владельца. Ошибка cleanup сохраняет запрет новых операций.
- ConnectionService получает owner в worker перед чтением профиля/engine.up.
  Начальный запуск, Auto/health scheduled actions, engine-down и stop callbacks
  исполняются с token. onDestroy освобождает owner только после успешного cleanup.
  Main-thread cancel остаётся немедленным и не ждёт owner/health network call.
  Служба, не получившая owner, при уничтожении не меняет глобальный статус чужой
  сессии. Disconnect без запущенной сессии завершает службу, не создавая owner.
- ProfileStore.save/clear входят в общий edit gate. При активной сессии даже прямой
  вызов store из другой Activity/thread отклоняется. После recovery callback ещё
  раз проверяется отсутствие восстановленной сессии, прежде чем менять профиль.
  Забывание профиля вынесено в Activity worker, чтобы UI не ждал owner/Keystore.
- Чтение ProfileStore больше не создаёт потерянный wrapping key. При неуспешном
  удалении файла ключ сохраняется; ошибка не выдаётся за успешное удаление профиля.
- ControlStatePresence/ControlMutationGate: legacy connect/save/clear отклоняются
  при любой control-identity/control-journal base/bak/new или соответствующем
  Keystore alias. Ошибка чтения Keystore также не разрешает mutation. Никакого
  auto-create, journal reset, очистки identity или downgrade floor.
- ControlTransaction.receive/recover требуют отсутствия legacy session owner.
  Иначе независимый вызов carrier мог бы изменить VPN между service callbacks,
  несмотря на общий mutex. ACK flush по-прежнему разрешён и не удерживает owner
  во время сети. Native управляемая сессия потребует отдельного согласованного
  service adapter: нельзя просто снять этот requireIdle или вызвать legacy save.

## Проверки

Контейнер gradle:8.11.1-jdk17 без сети; Android SDK35, прежние pinned BC1.85.2 /
Gson2.13.2 / JUnit4.13.2. javac компилирует все Java sources текущего Android app,
включая ConnectionService/MainActivity/ProfileStore и новые guards. Engine API и
R symbols берутся из ранее собранных /tmp/fc-control-ci app classes/R.jar;
движки/ресурсы заново не собирались, полная Gradle/ABI совместимость не заявляется.

JUnitCore: **33 tests passed,2.325s** (предыдущие23 +10 owner/presence tests).
Проверены: active lease между callbacks; stale cleanup; failed shutdown retaining
owner; отказ recovery до profile mutation; восстановление сессии внутри callback;
конкурентный import/claim с latches; запрет control receive/recover/manual во время
legacy session при разрешённом ACK flush; null owner; все6 файловых markers,
оба orphan aliases и ошибка Keystore-provider модели.

Сохранены все3 Python transaction transcripts/16 steps,30 config/15 ACK inputs,
32 structural/4 cipher refusals. Fixtures не менялись. Manifest SHA256
c97e00ccff7440b09a636a792557c0602aba5eb63815cdc8fefe7755711ac3cd.

Команда переносимых тестов: `gradle -p clients/android/control-tests test`.
В этой сессии direct javac/JUnitCore harness: /tmp/fc-android-owner/check.sh.
При компиляции остался warning отсутствующего androidx.annotation.RestrictTo$Scope
из cached dependency и note о deprecated API в прежнем VpnHealth. Это не чистая
full Gradle/lint build. Standalone source set исключает Android-only mutation gate
и оба vault; portable owner/state-presence покрыты JVM тестами.

## Границы и следующая работа

Это не Android runtime приёмка. JVM tests проверяют owner/gate; настоящие service
callbacks, engine shutdown, ProfileStore и Keystore/AtomicFile на устройстве пока
не запускались. На хосте нет /dev/kvm и установленного emulator image; physical
телефоны не использовались. Remote CI/инсталляция APK не выполнялись.

Managed state сейчас намеренно закрывает legacy connect/import/clear. Имеющийся
Android beta с ручными профилями не создаёт такую state; перед будущим enrollment
нужен native recovery/application adapter. Не включать создание identity/journal
в UI до этого адаптера. Не считать gate реализацией автоматического восстановления.

Далее: native service application adapter с trusted bounded snapshots,
transactional profile apply, network-bound traffic health и idempotent rollback;
startup recovery перед выдачей разрешения ручным действиям; isolated Android
Keystore/AtomicFile/process-death harness. Существующий worker/stop-destroy barrier
сохранить, второго VPN lifecycle не добавлять. Нужны реальные сценарии concurrent
import/connect, repeated stop, destroy/start, failed cleanup и revoked permission.
Если destroyed service оставил failed cleanup lease, в процессе gate сохраняется;
безопасное восстановление такого состояния — ещё критерий service runtime adapter,
не повод сбрасывать owner из нового экземпляра службы.

## Версии и возврат

Исходники не установлены на устройства. Android code3 / 0.1.2-beta03 не менялись;
новых APK/CI runs/release/catalog/tag/commit/server deployment нет. Никакие VPN,
профили, клиентские ключи или серверные службы этой сессией не менялись.

Изменения подготовлены в /tmp/fc-android-owner/tree; при записи в family_connect
проверяются SHA256 исходных файлов. Rollback кода: вернуть четыре изменённых app
classes и standalone exclude, убрать три новых owner/gate classes и их тест,
сохранив предыдущие identity/journal/ACK и все сторонние изменения. Не удалять
persisted control state/Keystore keys для обхода gate или rollback.
