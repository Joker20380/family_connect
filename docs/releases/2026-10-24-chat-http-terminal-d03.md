# D03 — ChatHTTP terminal errors и teardown, 24.10.2026

Вход: чистая `main`, HEAD = проверенный `origin/main`
`e3a0190893b0384980dc62b216951634e9319005`. Review D02.1 collection/import isolation
и D02.2 public-reference принят: зависимости D03 готовы. D02.1-R остаётся PARTIAL,
historical replay NOT_RUN из-за неподтверждённых retained artifact pins. D01/общий CI
открыт; D04 и D05 QUEUED, [fleet-контракт](../desktop-architecture.md#desktop-fleet-boundary) сохранён.
Code checkpoint **`290d43086bc0b1a00e9b53569fca4d7e3e12c08e`** отправлен обычным push;
`git ls-remote origin refs/heads/main` подтвердил тот же SHA. Проверенные production/test
bytes совпадают с commit. Последующий docs-only checkpoint содержит evidence этого SHA,
а не автоматически унаследованный CI PASS.
**D03 DONE по локальной логике; review pending, общий CI не закрыт.**

## Изменение

Только продуктовый `ChatHTTP.stream` в [chat_bridge.py](../../provisioning/chat_bridge.py):
первая уже установленная terminal-причина сохраняется **до** teardown. TLS при чтении
классифицируется до cleanup, поэтому собственный non-TLS cause cleanup её не скрывает;
invalid_response не заменяется TLS ошибкой закрытия. Сохраняются timeout и cancellation,
включая BaseException cancellation; неожиданные исключения не подавляются.

HTTPX `iter_bytes`/`iter_raw` закрывают response при EOF. После прежней строгой проверки
identity encoding читается raw `response.stream`, чтобы зафиксировать полное чтение
до закрытия через неизменённый `direct.stream` context manager. Close не обходится.
Завершённый 200 сохраняет полученные bytes при non-TLS TransportError cleanup, без
повторной отправки. TLS cleanup без предыдущей terminal-причины остаётся отказом;
unexpected cleanup error распространяется (FriendsClient даёт service_unavailable).
Семантическая/JSON валидация остаётся во FriendsClient, не переносится в ChatHTTP.

Единственный yield расположен вне direct exception handler. Ошибка потребителя после
yield не разрешает fallback. Прежние ConnectError/ReadTimeout/503, partial-read transient
fallback и BridgeError mapping сохранены; новых retry loops нет. Fixed paths, 8KiB request /
16KiB response bounds, identity encoding, no redirects, deadlines и публичные error codes
не менялись; приватные данные в диагностику не добавлялись.

## Воспроизведение и адресные проверки

Чистый export без state; non-root `/tmp/test-venv/bin/python` 3.13.15, неизменённый
D01.2 `scripts/ci_python313_env.sh`: httpx0.28.1, pytest9.1.1, PyGObject3.50.0;
strict real imports PASS. Raw локальные logs — `/tmp/fc-d03/evidence/`, не в Git.
Тестируется фактический ChatHTTP/FriendsClient через httpx.MockTransport и управляемый
SyncByteStream; метод не скопирован. Clock deadline управляемый, без sleeps.

| Команда / срез | Passed | Failed | Errors | Skipped |
|---|---:|---:|---:|---:|
| `python -m pytest -q tests/test_chat_bridge_http.py --tb=short`, старый production метод + новые regressions | 18 | 15 | 0 | 0 |
| Та же команда после исправления | 33 | 0 | 0 | 0 |
| `python -m pytest -q tests/test_friends_client.py clients/desktop/tests/test_chat_host_registration.py clients/desktop/tests/test_mesh_chat_host.py clients/desktop/tests/test_chat_service.py --tb=short -rs` | 63 | 0 | 0 | 0 |
| `python -m pytest -q messenger/tests/test_linux_owner.py messenger/tests/test_linux_mailbox.py --tb=short -rs`, на code SHA | 24 | 0 | 0 | 0 |

19 новых cases: HTTP400/401/403/409 + close error; encoding/bound + close; TLS read +
cleanup со своим cause; invalid_response + TLS/RuntimeError cleanup; установленный
deadline; полный 200/invalid JSON; consumer TransportError после yield; read cancellation
и Friends cancellation после чтения; unexpected cleanup; сохранение partial transient
fallback с успешным/неуспешным close. Fixture проверяет реальный close ровно один раз.
Существующие 14 direct-success/transient/denial/bounds cases сохранены.

## CI и границы

Фактический CI на **`290d430`**, не перенесённые counts D02.2:

| Job | Статус полного suite / job | Последующие gates |
|---|---|---|
| [control](https://github.com/Joker20380/family_connect/actions/runs/40086279075/job/120849770781) | FAIL: 2910 passed / 54 failed / 0 errors / 106 skipped | GUI/render, упаковка, extracted-package/recovery skipped |
| [phase0/tests](https://github.com/Joker20380/family_connect/actions/runs/40086279088/job/120849770695) | FAIL: 2910 passed / 54 failed / 0 errors / 106 skipped | cargo skipped |
| [Docker tests-stage / failover](https://github.com/Joker20380/family_connect/actions/runs/40086279088/job/120849770604) | FAIL: 2909 passed / 53 failed / 0 errors / 108 skipped | Маркер tests-passed/runtime image не созданы; provision/failover/auth/offline/revocation skipped |

В control/phase0 strict imports, D01 адресные gates и source-pinned release fixtures PASS;
Docker root 22 passed, адресные 59 passed, полный suite от runner. Во всех трёх полных
suites pytest exit1, по 7 passed subtests / 2 warnings. Docker artifact12557137135
`phase0-failover/build.log`: 3070 cases, ChatHTTP в FAILED list отсутствует. Остаточные
группы: historical capsule sources — 19, HTTP evidence/runtime/preflight/transition — 30,
native expiry — 2, private storage — 2; control/phase0 также readiness socket — 1.
Это отдельные failures, не D03; вариация socket/Auto не является их исправлением.

[Linux voice](https://github.com/Joker20380/family_connect/actions/runs/40086279063/job/120849770625)
на том же SHA — job **PASS**, actual codec/mailbox и synthetic GTK gates PASS, не installed/live
delivery acceptance. Несвязанные Android/Windows jobs не ожидались. Client builds/AWG/TCP
не запустились на этом SHA (существующие path filters); их прошлые PASS не перенесены сюда.
Полные CI suites и gates неизменны;
локально полный исторический pytest не запускался. Остальные capsule/HTTP/nginx/expiry/
privacy/socket failures и Auto не исправлялись и не подавлялись.

Версии Linux0.2.11 / Windows0.2.15 / Android106, accepted pins, D01 environments,
historical fixtures, IPC/network policy не менялись. Installed/live delivery,
protected DIRECT/service-only, полные installers, deployment/publication — NOT_RUN.
Установки не менялись; runtime rollback не требуется. NEXT — **review D03**, затем STOP;
D04/D05 и другие задачи автоматически не начинать.
