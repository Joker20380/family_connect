# Android Stage 5: explicit Reticulum enrollment — 14.09.2026

## Реализовано в исходниках

Продолжение resume по запросу пользователя. HEAD4cb1423/main, прежний большой
незакоммиченный Stage5 сохранён. Добавлены ControlEnrollment, Android storage adapter,
HTTPS transport и отдельный AES-GCM/Keystore/AtomicFile enrollment vault с собственным
alias и AAD family-connect/control-enrollment/v1, пределом plaintext16384 bytes.
Identity/WG secrets остаются в существующем device vault. Enrollment state хранит
schema/origin/phase/device/proof, не invitation token и не private keys.

Состояния INITIALIZING → READY → COMPLETING → ENROLLED. INITIALIZING записывается
перед identity/journal; частичная запись восстанавливается без неявной смены ключей.
Orphan/corrupt state отказывает, READY не создаёт пропавший journal заново.
Наличие прежних control state без enrollment metadata не означает разрешение
автоматически присвоить их новой регистрации. Нужен отдельный путь adoption.

Сохраняется постоянная Reticulum identity и независимый WG key. Пустой journal
инициализируется с packaged anchor и действительной package version. Перед сетью
все локальные записи проверяются чтением. Enrollment получает отдельный APP owner,
поэтому service/profile mutations не могут идти параллельно; сетевой запрос не
держит monitor ControlJournal.OWNER. Enrollment не запускает VPN engine.

Код использует существующие /v2/registration/challenge и /complete: public RNS identity,
WG public key, одноразовый challenge, audience и Ed25519 proof. Proof сохраняется
до complete. На повторе COMPLETING разрешена только повторная отправка того же
сохранённого proof. Серверный replay отказ не ослаблялся. При IOException/refusal
проверяется /v2/provisioning/challenge на том же HTTPS origin с теми же public keys.
Успешный ответ с audience family-connect/provisioning-fetch/v1 подтверждает, что
сервер знает эту привязку и сейчас разрешает provisioning. Это TLS-authenticated
проверка состояния, не новая подписанная VPN config и не bearer credential.
Подписанная config по-прежнему проверяется отдельным offline root/device/WG binding.

Если completion proof истёк до доставки, а сервер не подтверждает зарегистрированную
identity, состояние остаётся COMPLETING: автоматического нового challenge, переноса
на другой сервер или сброса ключей нет. Требуется операторское разрешение неопределённой
регистрации. Reconciliation расходует provisioning challenge; серверный лимит16
и TTL120s сохранены. ENROLLED означает сохранённый результат регистрации; повтор
не заявляет актуальную подписку и не проверяет её снова без provisioning flow.

## UI и сетевые границы

В MainActivity добавлена кнопка «Зарегистрировать устройство» и RU/EN диалог.
Пользователь явно вводит HTTPS origin оператора и приглашение64 lowercase hex.
До продолжения объясняется переход к managed VPN: ручной import/clear блокируются,
профили сохраняются, регистрация не поднимает VPN. Для retry нужен тот же origin;
в COMPLETING/ENROLLED token уже не нужен. Origin фиксируется до сетевого запроса,
его смена пока не поддержана, в том числе после ошибочного ввода действительного URL.

Ключи не уходят с устройства; token отправляется только в body challenge и не
сохраняется в state/preferences. Token временно существует в JVM String; полного
стирания JVM/IME copies не заявляем. Dialog защищён FLAG_SECURE, save/autofill полей
отключены; invitation скрыт password input. Ошибки не выводят token/proof/exception.
Существующие данные не удаляются. Activity destruction отменяет HTTP/worker;
реальная rotation/back/cancel приёмка ещё нужна.

HTTPS только через системную проверку сертификата/hostname; URL без userinfo/query/
fragment/path, разрешены только три фиксированных API paths. Redirect/cache выключены,
request/response ≤8192 bytes, Content-Type JSON, строгие UTF8/JSON/duplicate checks.
Connect/read timeout5s, отдельный watchdog15s с disconnect. Это cooperative cancellation,
не доказанная жёсткая15s граница DNS/OS I/O. Серверного HTTPS origin в приложение
не зашито: оператор должен предоставить доступный TLS ingress. Никакой live token
или endpoint в этой сессии не использовался.

ControlStatePresence учитывает новый enrollment base/bak/new и orphan alias, поэтому
прерывание даже до identity creation не допускает legacy bypass. Native managed
journal/apply/recover остаются отдельными от enrollment metadata.

## Проверки

Docker gradle:8.11.1-jdk17 --network none, Android35, BC1.85.2/Gson2.13.2/JUnit4.13.2.
Aapt2 compiled/linked RU/EN resources и сгенерировал свежий R.java с временным manifest
package. Скомпилированы все app Java, control/test Java с cached engine dependencies.
Resource-only package не является собранным приложением; engine/ABI/Gradle/lint не
пересобирались. Исходный trust asset побайтно не изменён; packaging assets в full APK
ещё требует проверки.

**81 Java tests passed,2.421s**: прежние63 плюс14 enrollment и4 HTTP tests.
Сценарии: proof/device binding, token не попадает в metadata, lost reply, crash before
complete, final write failure/retry, interrupted initialization, existing state,
origin/input rejection, wrong audience/receipt, cancellation/active VPN, corrupt proof,
AES-GCM domain/tamper/bounds, enrollment markers; HTTP method/no redirect/timeout/
body bound/duplicate JSON/cancel. HTTP connection fake, Android vault/runtime fake или
не исполняются: реального TLS сервера/Android OS end-to-end этим не доказано.

Промежуточная проверка после добавления повторного proof имела1 failure: тест
ENROLLED ошибочно ожидал второй запрос; исправлено ожидание (завершённая регистрация
не отправляет запрос), итог81/81. Прежние missing annotation Scope.LIBRARY_GROUP
warning и VpnHealth deprecated note остаются.

**57 Python tests passed,1.03s**: tests/test_android_control_identity.py,
tests/test_product_registration.py, tests/test_product_provisioning.py.
Проверены reference proof, API, одноразовость, лимиты/revoke/concurrency и provisioning.
2 прежних Starlette/httpx/AnyIO deprecation warnings. Python код/API не менялся.
Java immutable30 config/15 ACK/32 structural/4 cipher refusals прошли; manifest SHA256
c97e00ccff7440b09a636a792557c0602aba5eb63815cdc8fefe7755711ac3cd.

Harness: /tmp/fc-android-enrollment/check.sh; portable suite:
`gradle -p clients/android/control-tests test`.
Python: `/tmp/fc-provisioning-venv/bin/python -m pytest -q -p no:cacheprovider tests/test_android_control_identity.py tests/test_product_registration.py tests/test_product_provisioning.py`.

## Версии, оставшаяся работа и возврат

VersionCode3/versionName0.1.2-beta03 сохранены. Последний локально документированный
Android CI34776015693/source63831305f063350fd21af44c93d6a8bef122b795 относится к
прежнему APK SHA256 c6bb7df99d55a53a8da0d7fb9f177855976d91c6cf8b8bb1adf1fb652399649a.
Remote CI/deployment в этой сессии не проверялись. Нет нового application APK,
commit/tag/release/catalog/install, live enrollment или изменений серверов.

Далее isolated Android Keystore/AtomicFile/process-death/UI/TLS acceptance и full
Gradle/lint/ABI; signed Stage5 config/RNS carrier и ACK delivery. Существующий
product /v2/provisioning/fetch выдаёт другой provisioning envelope — нельзя считать
его готовым Stage5 control config или подавать в control.receive без правильного
protocol adapter. Нужны minimum-version policy, manual admission, managed Auto/AWG3.1.
Django/оплата пока архитектура; Messenger/iPhone отложены по PLAN.

Stage: /tmp/fc-android-enrollment/tree, snapshot до переноса:
/tmp/fc-android-enrollment/before. Перенос проверяет SHA256 исходников и отсутствие
новых destination files; сохраняет прочий незакоммиченный код. Source rollback:
восстановить MainActivity/strings/control-tests config, убрать новые enrollment classes
и tests, обновить STATUS/PLAN. Если enrollment state уже создан, ОБЯЗАТЕЛЬНО сохранить
расширение ControlStatePresence для enrollment markers/alias, чтобы не открыть legacy
после orphan INITIALIZING. Не удалять identity/journal/enrollment state и не снижать
replay floor. Runtime rollout отсутствует, новая сборка не устанавливалась.
