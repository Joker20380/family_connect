# Android Stage 5: journal, ACK и crash recovery — 14.09.2026

## Решение пользователя и исходное состояние

Сначала весь план VPN-сервиса Linux/Windows/Android. Мессенджер и iPhone после
завершения плана; существующие chat/prototype изменения сохраняются. Порядок
и шесть условий выпуска закреплены в PLAN/STATUS/ROADMAP/README.

Базовый checkout family_connect/main HEAD4cb1423, большой незакоммиченный Stage5
и последующая работа. Перед продолжением проверены git status и актуальные
STATUS/PLAN; предыдущий identity block и immutable fixtures использованы без
перегенерации. Изменения готовились и тестировались в /tmp/fc-android-journal/tree;
при переносе проверяются исходные SHA256 для защиты от параллельной перезаписи.
Соседний microtrader не менялся.

## Реализация

- ControlIdentity создаёт device-signed ACK с существующим ACK domain и canonical
  ack_id/body/signature. Canonical bytes совпадают с Python fixtures. Размерный
  fixture содержит хвостовые JSON-пробелы: сравнение компактного вывода удаляет
  только этот хвост; существующий verifier продолжает проверять4096-byte input.
- ControlJournal: local schema1, device binding, floor/last_now, committed/staged,
  baseline, phase, result и outbox. Максимум1MiB plaintext и64 ACK. Повторное чтение
  проверяет strict JSON, phase coherence, signatures исторических envelopes при
  сохранённом времени, digests, revisions, timestamps, device-signed ACK и duplicates.
  Добавлен local device field; файл не заявляется переносимым Python journal.
- ControlTransaction: STAGED → APPLYING → APPLIED_PENDING → IDLE; rollback intent
  ROLLING_BACK сохраняется прежде очистки. Сбой записи не даёт ложного COMMITTED.
  Commit pointer и COMMITTED ACK в одной atomic write. Floor после rollback не
  понижается; одинаковый wire envelope возвращает сохранённый результат без apply.
  Истечение lease проверяется после health и повторно после финального snapshot.
- Application contract требует read-only snapshot, idempotent rollback, настоящий
  traffic health и cleanup кандидата даже при истёкшем предыдущем lease.
  mayRestore=false запрещает восстановление просроченного committed профиля.
- Общий process-local OWNER сериализует receive/recover/manual. Manual hook сначала
  восстанавливает pending; неуспешный rollback блокирует новую mutation. Clock rollback
  также блокирует действие. Пока этот hook не используется реальными UI/service.
- ACK queue резервируется до apply. Flush получает bounded snapshot очереди, отпускает
  owner на network send, затем перечитывает актуальное состояние и удаляет только
  подтверждённые bytes. Сбой/перезапуск оставляет устойчивый retry; новые concurrent
  ACK не теряются. Параллельные отправители могут повторно отправить одинаковый ACK:
  relay idempotency обязательна. Sender обязан иметь deadline/cancellation; carrier
  пока не подключён, сам callback этот модуль прервать не может.
- ControlJournalEnvelope/Vault: отдельный AndroidKeyStore alias
  family-connect-control-journal-v1, AES256-GCM с собственным AAD,1-byte version,
 12-byte nonce,16-byte tag; максимум1MiB+29 ciphertext bytes. AtomicFile
  control-journal.enc в noBackupFilesDir. Explicit create отказывает при alias/base/
  bak/new; load/write не создают пропавший ключ/файл. После finishWrite сверяются
  прочитанные plaintext bytes. Orphan alias не удаляется для неявного повторного
  enrollment. Требуется один app process; защиты от root-level rollback всех данных
  или hardware monotonic counter не заявляется.

## Проверки

Локальный gradle:8.11.1-jdk17 контейнер без сети; BC1.85.2/Gson2.13.2/JUnit4.13.2
из прежнего cache. javac с Android SDK35 успешно компилирует Control classes,
включая два Android-only vault. JUnitCore: **23 tests passed,2.909s**.
Это прежние8 тестов и15 новых journal/transaction методов с дополнительными циклами.

- Все3 immutable Python transcripts,16 шагов: результат, active state, committed
  hash, floor, phase, количество apply/rollback, error и outbox.
- Старые30 configurations,15 ACK,32 structural refusals,4 authenticated cipher refusals.
  Manifest SHA256 c97e00ccff7440b09a636a792557c0602aba5eb63815cdc8fefe7755711ac3cd.
- Восемь сценариев process-death модели: до/после каждой из четырёх durable write
  границ успешной транзакции; четыре дополнительных сбоя на rollback write boundaries.
- Повторная доставка, replay/previous-hash, apply/health failure, rollback failure
  и manual gate, lease expiry во время health и финального snapshot, clock regression.
- Offline/partial ACK delivery с точными bytes после restart. Отдельный worker получает
  следующую конфигурацию, пока sender исполняется; проверено отсутствие owner deadlock
  и сохранение новых ACK после удаления старых.
- Saturated outbox отказывает до snapshot/apply. Повреждённые/missing journal,
  bool schema/floor, чужая identity/ACK, неверные timestamps/digests, duplicate ACK
  отклоняются без VPN mutation. Encryption boundaries, corruption и domain separation.

Повторение переносимых тестов: `gradle -p clients/android/control-tests test`.
В этой сессии использованы прямые javac/JUnitCore в /tmp/fc-android-journal/check.sh;
standalone Gradle source set исключает ControlIdentityVault/ControlJournalVault,
которые требуют Android SDK. Полный Gradle APK/lint/emulator/remote CI не запускались.
Python-код и fixtures не менялись; прошлые51 Python tests — результат предыдущего
identity checkpoint, не новый запуск этой сессии.

## Что ещё не принято

Memory storage и Error fault injection моделируют crash; это не настоящий Android
process kill/fsync тест. Keystore/AtomicFile проверены компиляцией, не исполнением.
Нужен isolated runtime harness: explicit enrollment, process restart/load, missing
alias/file, corruption, interrupted write, отсутствие ложного reset floor/commit.
Read-back обнаруживает несовпадение записи, но не заменяет испытание power loss.

Activity, ConnectionService, ProfileStore, Auto callbacks и stop/destroy barrier
не менялись. Поэтому journal owner пока не защищает существующие ручные действия
и не используется live VPN. Не подключать RNS receive к этому коду до общего
service ownership/recovery/native adapter. Snapshot должен описывать только
доверенные локальные профили; candidate не может задавать privileged path.

Далее: интегрировать существующий service worker, import/clear и lifecycle callbacks
с общим владельцем операций и startup recovery; принять protected storage runtime;
затем native apply/traffic health/rollback и RNS carrier. Windows Stage5, signed
AWG3.1, независимый Stage6 и остальные условия выпуска остаются открыты.

## Версии, rollout и rollback

Android versionCode3 / 0.1.2-beta03 не менялись. Новых APK, CI run, commits/tags,
release/catalog, server deployment или device install нет. Существующие VPS/VPN
и физические устройства не затронуты; private state в Git/вывод не попадало.
Это исходники до wiring: runtime rollback не требуется. Для отмены этого блока
убрать новые ControlJournal*/ControlTransaction и новый тест, вернуть добавленный
ACK метод ControlIdentity и standalone exclude, сохранив предыдущий identity block
и остальные незакоммиченные изменения. Не удалять будущий журнал/Keystore alias
для обхода recovery или понижения revision floor.
