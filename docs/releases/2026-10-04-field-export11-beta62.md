# FIELD export(11): beta62 first failure and recovery policy, 2026-10-04

Follow-up: [local recovery classification patch and regression results](2026-10-04-restricted-recovery-classification.md)
are now recorded separately. The analysis below describes the installed beta62 behavior;
the patch is not installed or distributed, and does not fix the original DATA stall.

## Результат

Экспорт `FamilyConnect-diagnostics(11).json`, SHA256
`df2fc50c26e3a51b51eec74a7f3511f79815ddd3f00a0ec8109bf6c8f16e6d2e`,
принадлежит FC-YHQB-9VJN,0.1.18-beta62/code62; network_class CELLULAR.
Это уже полученная мобильная репродукция, не ожидание следующего теста.
Сохранены четыре restricted-сеанса: исторический13:17 и три новых15:05–15:12UTC.
Не считать их одной попыткой; новых повторов сейчас не требуется.

Серверное чтение Amsterdam выполнено read-only: конкретный текущий journal-файл,
только restricted-bootstrap unit и13:16–15:14UTC, лимиты40s/15000 строк/12MiB.
Сохранены только allowlisted restricted_trace записи выбранных session_tag.
Все четыре связи Support/connection/incident/session_tag находятся offline-коррелятором;
привязка этих идентификаторов берётся из клиентского экспорта, не заменяет авторизацию.
Серверные последовательности полные, без gaps. Native/client ring ограничен по размеру;
число клиентских событий не означает полный пакетный журнал.

| Session tag (prefix; full tags below) | Client/server events | Первый клиентский сбой, UTC | Первый серверный сбой, UTC |
| --- | --- | --- | --- |
|16438408|32/65|13:18:04.132 RETRY_EXHAUSTED|13:18:10.852 RETRY_EXHAUSTED|
|d5048440|28/40|15:05:21.683 SIGNAL_WS_CLOSE / READ_ERROR|15:05:33.300 RELIABLE_HANDSHAKE_TIMEOUT|
|f6990ce1|32/72|15:07:10.843 RELIABLE_RETRY_EXHAUSTED|15:07:39.638 RELIABLE_RETRY_EXHAUSTED|
|f9c72153|43/72|15:11:46.001 RELIABLE_RETRY_EXHAUSTED|15:12:14.475 RELIABLE_RETRY_EXHAUSTED|

Полные tags, без усечения в корреляции:

- `16438408f948ddcbb1202db82870b235ddca49ba83aeef26bb4df97cff2205ca`
- `d5048440270c7351e416ad31d893cd57d83a0fbb68d960ec994027342b90d089`
- `f6990ce16e5ff08dc14b19c414876daa4ace4f27ac609d1818808b543bcfd2a2`
- `f9c7215316f1d7e5a58ff365926238a02877f81cf18f25273d498075f03cd0d9`

## Два новых установленных сеанса

Для f699/f9c7 обе стороны подтверждают Family TLS и gateway session established,
двунаправленный carrier и heartbeat. Native first_failure записан до LOCAL_CLOSE
и последующих FAMILY_TLS_ERROR. Это не ошибка первого входа/приглашения и не истечение
сертификата: серверная граница17:30:19UTC существенно позже обоих сбоев, readiness READY.

| Клиентский terminal counter | f699 | f9c7 |
| --- | ---: | ---: |
| Возраст блока, ms |9410|9416|
| Повторные передачи выбранного блока |8|8|
| Outstanding blocks |8|8|
| Последний принятый non-stale ACK, ms назад |428|1527|
| Последнее cumulative продвижение, ms назад |8155|7886|
| Получено ACK всего |49|66|

По `carrier/reliablestream/engine.go` это именно ветка MaxRetries, не MaxAge20s
и не SACKed-but-unconsumed timeout: выбранный блок не был SACKed.
Свежие ACK при отсутствии cumulative progress исключают объяснение «совсем перестали
приходить любые ответы». Но они не доказывают, где потерялись DATA/фрагменты либо их
подтверждения. Нельзя утверждать, что виноваты РКН, конкретный оператор, SFU, размер
пакета или алгоритм сборки. Нужны направленные локальные loss/reorder/ACK/framing
регрессии и при необходимости числовая, без payload/секретов, диагностика этого участка.
Не увеличивать retry/window/RTO наугад и не объявлять дефект исправленным.

Отдельный d504 сеанс падает до установленного Family TLS: первым клиентским событием
является WEBSOCKET CLOSED/READ_ERROR без точного peer close code. Сервер впоследствии
исчерпывает20s handshake. Это отдельный наблюдаемый путь отказа, не доказательство
той же причины, что у двух уже установленных сеансов.

Межхостовые часы не используются как строгое доказательство причинности. Причинный
порядок на клиенте доказан sequence: retry failure → local close → TLS cleanup errors.
Позднейшие серверные ошибки не подменяют первый клиентский failure.

## Почему автоматическое восстановление не начинается

Есть отдельная конкретная ошибка классификации recovery:

- `AutomaticConnection.java:98`: любой unhealthy restricted передаётся как INTERNAL.
- `ConnectivityOrchestrator.java:78` и`:120`: INTERNAL терминален; после события
  restoration_attempted выполняется finish/cleanup вместо нового run.
- В обоих экспортах policy_reason INTERNAL, cleanup_completed, restoration_failed,
  restricted_descriptor NOT_ATTEMPTED. Для последнего сеанса это15:11:51.114–51.409UTC.
- `DiagnosticRing.java:45` показывает точную native-причину вместо INTERNAL только
  в диагностике; политика восстановления от этой подмены не меняется.

Это объясняет отсутствие новой попытки после разрыва, **но не первичный застой DATA**.
Следующая коррекция должна явно отделить восстанавливаемый транспортный отказ от
AUTH/expiry/revocation/configuration/cancellation/неизвестного INTERNAL, сохранить
bounded recovery, cleanup-before-new-descriptor и fail-closed защиту. Нельзя просто
переклассифицировать любой unhealthy в NETWORK. В этой проверке код поведения не менялся.

## Проверки, сохранность и следующий шаг

- Offline assertions PASS: четыре session tags, четыре направления поиска каждого,
  gap-free server traces; два новых established сеанса с first failure до cleanup,
  точными retry/ACK counters и подтверждённым INTERNAL/NOT_ATTEMPTED recovery.
- Client forbidden-marker scan и строгая server-trace allowlist PASS; raw journal
  не выводился и не сохранялся как публичный отчёт. Это проверка экспортированной
  диагностики, не аудит всех данных приложения/сервера.
- Private receipts: `state-client-build/field62-export11/{summary,correlation,journal-receipt}.json`.
  Начальный sandbox SSH отказ не изменил сервер; одобренное read-only чтение успешно.
- APK/серверный runtime не менялись, сборок/подписей/установок/renewal не было.
  Поэтому новый rollout/rollback не выполнялся; остаётся
  [ранее принятый rollout/rollback](2026-10-04-beta62-four-hour-rollout.md).
- Принятая beta62: source `42a5e59b4bc2c43e56e018ce7287cd7b6e901db2`, APK SHA256
  `f60b8d3a74b85a5934b942d7e273831e7c1d88d35e4d8a87db7332fb7d7703d4`, signer
  `67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a`.
  Beta60 default/catalog, FIELD admission, Support IDs и прочие платформы не менялись.

NEXT: локально проверить и исправить доказанную recovery-классификацию с регрессиями;
отдельно локализовать отсутствие DATA progress при продолжающихся ACK. Перед новой
поставкой обязательны platform CI, immutable version/signing, owner in-place acceptance
и проверка реального оставшегося окна. Пользовательский повтор сейчас не нужен.
